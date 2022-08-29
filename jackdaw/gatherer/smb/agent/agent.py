import asyncio
import traceback
import random

from jackdaw.dbmodel.netshare import NetShare
from jackdaw.dbmodel.netsession import NetSession
from jackdaw.dbmodel.localgroup import LocalGroup
from jackdaw.dbmodel.smbfinger import SMBFinger
from jackdaw.dbmodel.smbprotocols import SMBProtocols
from jackdaw.dbmodel.regsession import RegSession
from jackdaw.dbmodel.smbinterface import SMBInterface
from jackdaw.dbmodel.smbfile import SMBFile
from aiosmb.protocol.common import SMB_NEGOTIATE_PROTOCOL_TEST, NegotiateDialects
from aiosmb.commons.utils.extb import format_exc
from aiosmb.commons.interfaces.machine import SMBMachine


from jackdaw import logger

# https://stackoverflow.com/questions/1094841/get-human-readable-version-of-file-size
def sizeof_fmt(num, suffix='B'):
	if num is None:
		return ''
	for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
		if abs(num) < 1024.0:
			return "%3.1f%s%s" % (num, unit, suffix)
		num /= 1024.0
	return "%.1f%s%s" % (num, 'Yi', suffix)

class AIOSMBGathererAgent:
	def __init__(self, in_q, out_q, smb_mgr, gather = ['all'], localgroups = [], concurrent_connections = 10, protocols = [NegotiateDialects.WILDCARD], share_max_files = 100):
		self.in_q = in_q
		self.out_q = out_q
		self.smb_mgr = smb_mgr
		self.gather = gather
		self.localgroups = localgroups
		self.protocols = protocols
		self.concurrent_connections = concurrent_connections
		self.share_max_files = share_max_files

		self.worker_tasks = []
		self.targets = []
		self.worker_q = None
		self.host_max_wait = 60

		self.regusers_filter = {
			'S-1-5-19' : 1,
			'S-1-5-20' : 1,
			'S-1-5-18' : 1,
		}

	async def scan_host(self, atarget):
		try:
			tid, target = atarget
			connection = self.smb_mgr.create_connection_newtarget(target)
			async with connection:
				_, err = await connection.login()
				if err is not None:
					raise err

				machine = SMBMachine(connection)


				if 'all' in self.gather or 'shares' in self.gather:
					async for smbshare, err in machine.list_shares():
						if err is not None:
							await self.out_q.put((tid, connection.target, None, 'Failed to list shares. Reason: %s' % format_exc(err)))
							break
						else:
							share = NetShare()
							share.machine_sid = tid
							share.ip = connection.target.get_ip_or_hostname()
							share.netname = smbshare.name
							share.type = smbshare.type
							await self.out_q.put((tid, connection.target, share, None))
					
				
				if 'all' in self.gather or 'sessions' in self.gather:
					async for session, err in machine.list_sessions():
						if err is not None:
							await self.out_q.put((tid, connection.target, None, 'Failed to get sessions. Reason: %s' % format_exc(err)))
							break
						else:
							try:
								sess = NetSession()
								sess.machine_sid = tid
								sess.source = connection.target.get_ip_or_hostname()
								sess.ip = session.ip_addr.replace('\\','').strip()
								sess.username = session.username

								await self.out_q.put((tid, connection.target, sess, None))
							except Exception as e:
								await self.out_q.put((tid, connection.target, None, 'Failed to format session. Reason: %s' % format_exc(e)))
				if 'all' in self.gather or 'localgroups' in self.gather:
					for group_name in self.localgroups:
						async for domain_name, user_name, sid, err in machine.list_group_members('Builtin', group_name):
							if err is not None:
								await self.out_q.put((tid, connection.target, None, 'Failed to poll group memeberships. Reason: %s' % format_exc(err)))
								break
							else:
								lg = LocalGroup()
								lg.machine_sid = tid
								lg.ip = connection.target.get_ip_or_hostname()
								lg.hostname = connection.target.get_hostname()
								lg.sid = sid
								lg.groupname = group_name
								lg.domain = domain_name
								lg.username = user_name
								await self.out_q.put((tid, connection.target, lg, None))
				
				if 'all' in self.gather or 'regsessions' in self.gather:
					users, err = await machine.reg_list_users()
					if err is not None:
						await self.out_q.put((tid, connection.target, None, 'Failed to get sessions. Reason: %s' % format_exc(err)))
						
					else:
						try:
							for usersid in users:
								if usersid in self.regusers_filter:
									continue
								if usersid.find('_') != -1:
									continue
								sess = RegSession()
								sess.machine_sid = tid
								sess.user_sid = usersid

								await self.out_q.put((tid, connection.target, sess, None))
						except Exception as e:
							await self.out_q.put((tid, connection.target, None, 'Failed to format session. Reason: %s' % format_exc(e)))
			
				if 'all' in self.gather or 'interfaces' in self.gather:
					interfaces, err = await machine.list_interfaces()
					if err is not None:
						await self.out_q.put((tid, connection.target, None, 'Failed to get interfaces. Reason: %s' % format_exc(err)))
						
					else:
						try:
							for interface in interfaces:
								iface = SMBInterface()
								iface.machine_sid = tid
								iface.address = interface['address']

								await self.out_q.put((tid, connection.target, iface, None))
						except Exception as e:
							await self.out_q.put((tid, connection.target, None, 'Failed to format interface. Reason: %s' % format_exc(e)))
				
				if 'all' in self.gather or 'share_1' in self.gather:
					ctr = self.share_max_files
					maxerr = 10
					async for obj, otype, err in machine.enum_all_recursively(depth = 1, fetch_share_sd = False, fetch_dir_sd = True):
						otype = otype.lower()
						ctr -= 1
						if ctr == 0:
							break

						if err is not None:
							await self.out_q.put((tid, connection.target, None, 'Failed to perform first-level file enum. Reason: %s' % format_exc(err)))
							break
							
						else:
							try:
								if otype == 'share':
									continue
								if otype in ['file', 'dir']:
									sf = SMBFile()
									sf.machine_sid = tid
									sf.unc = obj.unc_path
									sf.otype = otype
									sf.creation_time = obj.creation_time
									sf.last_access_time = obj.last_access_time
									sf.last_write_time = obj.last_write_time
									sf.change_time = obj.change_time
									if obj.security_descriptor is not None and obj.security_descriptor != '':
										sf.sddl = obj.security_descriptor.to_sddl()
									if otype == 'file':
										sf.size = obj.size
										sf.size_ext = sizeof_fmt(sf.size)

									await self.out_q.put((tid, connection.target, sf, None))
							except Exception as e:
								maxerr -= 1
								await self.out_q.put((tid, connection.target, None, 'Failed to format file result. Reason: %s' % format_exc(e)))
								if maxerr == 0:
									await self.out_q.put((tid, connection.target, None, 'File Results too many errors. Reason: %s' % format_exc(e)))
									break
			
			try:
				if 'all' in self.gather or 'finger' in self.gather:
					connection = self.smb_mgr.create_connection_newtarget(target)
					extra_info, err = await connection.fake_login()
					if extra_info is not None:
						f = SMBFinger.from_fake_login(tid, extra_info.to_dict())
						await self.out_q.put((tid, connection.target, f, None))
			except Exception as e:
				await self.out_q.put((tid, connection.target, None, 'Failed to get finger data. Reason: %s' % format_exc(e)))
			
			
			try:
				if 'all' in self.gather or 'protocols' in self.gather:
					for protocol in self.protocols:
						connection = self.smb_mgr.create_connection_newtarget(target)
						res, _, _, _, err = await connection.protocol_test([protocol])
						if err is not None:
							raise err
						if res is True:
							pr = SMBProtocols()
							pr.machine_sid = tid
							pr.protocol = protocol.name if protocol != NegotiateDialects.WILDCARD else 'SMB1'
							await self.out_q.put((tid, connection.target, pr, None))
			except Exception as e:
				await self.out_q.put((tid, connection.target, None, 'Failed to enumerate supported protocols. Reason: %s' % format_exc(e)))
			
		except asyncio.CancelledError:
			return

		except Exception as e:
			await self.out_q.put((tid, connection.target, None, 'Failed to connect to host. Reason: %s' % format_exc(e)))
			return

		finally:
			await self.out_q.put((tid, connection.target, None, None)) #target finished

	async def worker(self):
		try:
			while True:
				target = await self.worker_q.get()
				if target is None:
					return
				await asyncio.sleep(random.random()*2.0) # adding delay because remote proxy might get stuck
				try:
					await asyncio.wait_for(self.scan_host(target), self.host_max_wait)
				except asyncio.TimeoutError:
					continue
				except Exception as e:
					#exception should be handled in scan_host
					continue
					
		except asyncio.CancelledError:
			return
		except Exception as e:
			logger.debug('SMB WORKER ERROR %s' % str(e))
			return

	async def terminate(self):
		for worker in self.worker_tasks:
			worker.cancel()

	async def run(self):
		"""
		Reads targets from queue and scans them
		"""
		try:
			#asylogger.setLevel(1)
			self.worker_q = asyncio.Queue()
			
			for _ in range(self.concurrent_connections):
				self.worker_tasks.append(asyncio.create_task(self.worker()))
				await asyncio.sleep(0)

			while True:
				target = await self.in_q.get()
				if target is None:
					for _ in range(self.concurrent_connections):
						await self.worker_q.put(None)
					break
				else:
					await self.worker_q.put(target)

			results = await asyncio.gather(*self.worker_tasks, return_exceptions = True)
			for res in results:
				if isinstance(res, Exception):
					logger.debug('SMB worker task error %s' % str(res))
			await self.out_q.put(None)
		except Exception as e:
			logger.debug('SMB worker manager error %s' % str(e))

