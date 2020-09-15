import asyncio
import traceback

from jackdaw.dbmodel.netshare import NetShare
from jackdaw.dbmodel.netsession import NetSession
from jackdaw.dbmodel.localgroup import LocalGroup
from jackdaw.dbmodel.smbfinger import SMBFinger
from jackdaw.dbmodel.smbprotocols import SMBProtocols
from aiosmb.protocol.common import SMB_NEGOTIATE_PROTOCOL_TEST, NegotiateDialects
from aiosmb.commons.utils.extb import format_exc
from aiosmb.commons.interfaces.machine import SMBMachine

from jackdaw import logger

class AIOSMBGathererAgent:
	def __init__(self, in_q, out_q, smb_mgr, gather = ['all'], localgroups = [], concurrent_connections = 10, protocols = [NegotiateDialects.WILDCARD]):
		self.in_q = in_q
		self.out_q = out_q
		self.smb_mgr = smb_mgr
		self.gather = gather
		self.localgroups = localgroups
		self.protocols = protocols
		self.concurrent_connections = concurrent_connections

		self.worker_tasks = []
		self.targets = []
		self.worker_q = None

	async def scan_host(self, atarget):
		try:
			tid, target = atarget

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


			connection = self.smb_mgr.create_connection_newtarget(target)
			async with connection:
				_, err = await connection.login()
				if err is not None:
					raise err
				
				try:
					extra_info = connection.get_extra_info()
					if extra_info is not None:
						f = SMBFinger.from_extra_info(tid, extra_info)
						await self.out_q.put((tid, connection.target, f, None))
				except Exception as e:
					await self.out_q.put((tid, connection.target, None, 'Failed to get finger data. Reason: %s' % format_exc(e)))

				machine = SMBMachine(connection)


				if 'all' in self.gather or 'shares' in self.gather:
					async for smbshare, err in machine.list_shares():
						if err is not None:
							await self.out_q.put((tid, connection.target, None, 'Failed to list shares. Reason: %s' % format_exc(err)))
							break
						else:
							share = NetShare()
							share.machine_sid = tid
							share.ip = connection.target.get_ip()
							share.netname = smbshare.name
							share.type = smbshare.type
							#share.remark = smbshare.remark
							#if smbshare.remark is not None:
							#	r = None
							#	try:
							#		r = smbshare.remark.decode('utf-16-le')
							#	except:
							#		try:
							#			r = smbshare.remark.decode('latin-1')
							#		except:
							#			try:
							#				r = smbshare.remark.decode('utf-8')
							#			except:
							#				r = smbshare.remark
							#	
							#	if isinstance(r, str):
							#		r = r.replace('\x00','')
							#		share.remark = r


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
								sess.source = connection.target.get_ip()
								sess.ip = session.ip_addr.replace('\\','').strip()
								sess.username = session.username

								await self.out_q.put((tid, connection.target, sess, None))
							except Exception as e:
								await self.out_q.put((tid, connection.target, None, 'Failed to format session. Reason: %s' % format_exc(e)))

				if 'all' in self.gather or 'localgroups' in self.gather:
					for group_name in self.localgroups:
						async for domain_name, user_name, sid, err in machine.list_group_members('Builtin', group_name):
							if err is not None:
								await self.out_q.put((tid, connection.target, None, 'Failed to connect to poll group memeberships. Reason: %s' % format_exc(err)))
								break
							else:
								lg = LocalGroup()
								lg.machine_sid = tid
								lg.ip = connection.target.get_ip()
								lg.hostname = connection.target.get_hostname()
								lg.sid = sid
								lg.groupname = group_name
								lg.domain = domain_name
								lg.username = user_name
								await self.out_q.put((tid, connection.target, lg, None))
		
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
				try:
					await asyncio.wait_for(self.scan_host(target), 20)
				except:
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
			self.worker_q = asyncio.Queue()
			
			for _ in range(self.concurrent_connections):
				self.worker_tasks.append(asyncio.create_task(self.worker()))

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

