import asyncio
import traceback

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

class AIOSMBFileGathererAgent:
	def __init__(self, in_q, out_q, smb_mgr, depth = 3, fetch_share_sd = False, fetch_dir_sd = False, fetch_file_sd = False, max_entries = None, concurrent_connections = 100):
		self.in_q = in_q
		self.out_q = out_q
		self.smb_mgr = smb_mgr
		self.depth = depth
		self.fetch_share_sd = fetch_share_sd
		self.fetch_dir_sd = fetch_dir_sd
		self.fetch_file_sd = fetch_file_sd
		self.max_entries = max_entries
		self.concurrent_connections = concurrent_connections


		self.worker_tasks = []
		self.targets = []
		self.worker_q = None
		self.host_max_wait = 60
		self.host_max_errors = 10

	async def enum_host(self, atarget):
		connection = None
		try:
			tid, target = atarget

			connection = self.smb_mgr.create_connection_newtarget(target)
			async with connection:
				_, err = await connection.login()
				if err is not None:
					raise err

				machine = SMBMachine(connection)
				maxerr = self.host_max_errors
				async for obj, otype, err in machine.enum_all_recursively(depth = self.depth, fetch_share_sd = self.fetch_share_sd, fetch_dir_sd = self.fetch_dir_sd, fetch_file_sd=self.fetch_file_sd, maxentries = self.max_entries):
					otype = otype.lower()
					if err is not None:
						await self.out_q.put((tid, connection.target, None, 'Failed to perform file enum. Reason: %s' % format_exc(err)))
						break
							
					else:
						try:
							if otype not in ['share', 'file', 'dir']:
								continue
							
							sf = SMBFile()
							sf.machine_sid = tid
							sf.unc = obj.unc_path
							sf.otype = otype

							if otype == 'share':
								continue
							
							if otype in ['file', 'dir']:
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
					await self.enum_host(target)
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

