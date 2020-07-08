import asyncio
import logging
import json
import traceback
import ipaddress
import multiprocessing
import threading
import enum
import copy

from tqdm import tqdm
from aiosmb.commons.interfaces.share import SMBShare
from aiosmb.commons.interfaces.file import SMBFile
from aiosmb.commons.interfaces.directory import SMBDirectory
from aiosmb.commons.connection.url import SMBConnectionURL

import aiosmb
from aiosmb.commons.utils.extb import format_exc

from jackdaw.common.apq import AsyncProcessQueue
from jackdaw.dbmodel.netshare import NetShare
from jackdaw.dbmodel.netdir import NetDir
from jackdaw.dbmodel.netfile import NetFile
from jackdaw.dbmodel.netdacl import NetDACL
from jackdaw import logger
from jackdaw.dbmodel import create_db, get_session

from jackdaw.dbmodel.adinfo import ADInfo
from jackdaw.dbmodel.adcomp import Machine

class SMBShareGathererCmd(enum.Enum):
	START = 'START'
	END = 'END'
	TERMINATE = 'TERMINATE'

# only using share settings, making it more granular (per dir, per file) would cause massive overload
# on some systems with a lot of files available
class SMBShareGathererSettings:
	def __init__(self, ad_id, smb_mgr, share_id, target, smbshare):
		self.ad_id = ad_id
		self.smb_mgr = smb_mgr
		self.share_id = share_id
		self.target = target
		self.share = smbshare
		
		#self.dir_only = True
		self.dir_depth = 5
		self.dir_name_filter = None
		self.dir_with_sd = True

		#self.file_with_data = False
		self.file_with_sd = True
		#self.file_name_filter = None

class SMBEnumError:
	def __init__(self, settings, error):
		self.error = error
		self.settings = settings

class SMBShareGathererResult:
	def __init__(self, result, settings):
		self.result = result
		self.settings = settings
		self.type = self.get_type()

	def get_type(self):
		if isinstance(self.result, SMBDirectory):
			return 'dir'
		else:
			return 'unknown'


class ShareGathererProcess(multiprocessing.Process):
	def __init__(self, in_q, out_q, worker_cnt):
		multiprocessing.Process.__init__(self)
		self.workers = []
		self.worker_cnt = worker_cnt
		self.in_q = in_q
		self.out_q = out_q
		self.semaphore = None

		self.main_task = None
		self.stop_task = None
	############# Enumerator worker

	async def enum_directory(self, connection, settings, directory, depth):
		try:
			await directory.list(connection)
			for name in directory.subdirs:
				if settings.dir_with_sd == True:
					await directory.subdirs[name].get_security_descriptor(connection)

			for name in directory.files:
				if settings.file_with_sd == True:
					await directory.files[name].get_security_descriptor(connection)

			res = SMBShareGathererResult(directory, settings)
			await self.out_q.coro_put(res)
			if depth == 0:
				return
			for name in directory.subdirs:
				await self.enum_directory(connection, settings, directory.subdirs[name], depth - 1)

		except asyncio.CancelledError:
			return

		except:
			traceback.print_exc()
			await self.out_q.coro_put(SMBEnumError(settings, traceback.format_exc()))

	async def enum_share(self, settings):
		try:
			connection = settings.smb_mgr.create_connection_newtarget(settings.target)
			await connection.login()
			#print('login ok!')
			await settings.share.connect(connection)
			#print('share ok!')
			await self.enum_directory(connection, settings, settings.share.subdirs[''], settings.dir_depth)
			#print('list ok!')

		except asyncio.CancelledError:
			return

		except:
			await self.out_q.coro_put(SMBEnumError(settings, traceback.format_exc()))

		finally:
			self.semaphore.release()


	################### Manager logic

	async def setup(self):
		self.semaphore = asyncio.Semaphore(self.worker_cnt)

	async def terminate(self):
		#print('terminating')
		for worker_task in self.workers:
			worker_task.cancel()

		if self.stop_task:
			self.stop_task.cancel()
		self.main_task.cancel()

	async def stop(self):
		for worker_task in self.workers:
			await worker_task
		await self.terminate()
		return

	async def main(self):
		await self.setup()
		while True:
			data_in = await self.in_q.coro_get()
			#print('process got data!')
			if data_in[0] == SMBShareGathererCmd.TERMINATE:
				await self.terminate()
				return
			elif data_in[0] == SMBShareGathererCmd.START:
				await self.semaphore.acquire()
				self.workers.append(asyncio.create_task(self.enum_share(data_in[1])))
			elif data_in[0] == SMBShareGathererCmd.END:
				self.stop_task = asyncio.create_task(self.stop())

	async def a_run(self):
		try:
			self.main_task = asyncio.create_task(self.main())
			await self.main_task
		except asyncio.CancelledError:
			return
		except:
			await self.out_q.coro_put(SMBEnumError(None, traceback.format_exc()))
		finally:
			await self.out_q.coro_put(None)
		
	def run(self):
		asyncio.run(self.a_run())

class ShareGathererManager:
	def __init__(self, settings_base, db_conn = None, db_session = None, worker_cnt = 30):
		self.settings_base = settings_base
		self.in_q = AsyncProcessQueue()
		self.out_q = AsyncProcessQueue()
		self.worker_cnt = worker_cnt
		self.targets_thread = None
		self.db_conn = db_conn
		self.db_session = db_session
		self.dir_lookup = {}
		self.exclude_shares = ['IPC$']

		self.use_progress_bar = True
		self.prg_dirs = None
		self.prg_files = None
		self.prg_errors = None
	
	def generate_targets(self):
		session = get_session(self.db_conn)
		qry = session.query(
			Machine.sAMAccountName, NetShare.id, NetShare.netname
			).filter(Machine.ad_id == self.settings_base.ad_id
			).filter(Machine.id == NetShare.machine_id)

		for mname, shareid, sharename in qry.all():
			if sharename in self.exclude_shares:
				continue
			target = mname if mname[-1] != '$' else mname[:-1]
			fullpath = '\\\\%s\\%s' % (target, sharename)
			smbshare = SMBShare(fullpath = fullpath)

			#print(target)
			#print(fullpath)
			#print(smbshare)

			settings = copy.deepcopy(self.settings_base)
			settings.share_id = shareid
			settings.target = target
			settings.share = smbshare
			self.in_q.put(( SMBShareGathererCmd.START, settings))

		session.close()
		self.in_q.put(( SMBShareGathererCmd.END, None))

	def init_dbsession(self):
		if self.db_session is not None:
			return
		self.db_session = get_session(self.db_conn)
	
	def setup(self):
		self.init_dbsession()
		self.targets_thread = threading.Thread(target = self.generate_targets)
		self.targets_thread.daemon = True
		self.targets_thread.start()

		self.gatherer = ShareGathererProcess(self.in_q, self.out_q, self.worker_cnt)
		self.gatherer.start()

		if self.use_progress_bar is True:
			self.prg_dirs = tqdm(desc='Dirs', ascii = True)
			self.prg_files = tqdm(desc='files', ascii = True)
			self.prg_errors = tqdm(desc='Errors', ascii = True)

	def get_dir_id(self, unc_path, name):
		#print(name)
		if name == '' or name is None:
			return None
		# this might get extended later!
		return self.dir_lookup[unc_path]

	def store_sd(self, sd, object_type, object_id):
		if sd is None:
			return
		order_ctr = 0
		for ace in sd.Dacl.aces:
			acl = NetDACL()
			acl.object_id = object_id
			acl.object_type = object_type
			acl.owner_sid = str(sd.Owner)
			acl.group_sid = str(sd.Group)
			acl.ace_order = order_ctr
			
			order_ctr += 1
			acl.sd_control = sd.Control
			
			acl.ace_type = ace.Header.AceType.name
			acl.ace_mask = ace.Mask
			t = getattr(ace,'ObjectType', None)
			if t:
				acl.ace_objecttype = str(t)
			
			t = getattr(ace,'InheritedObjectType', None)
			if t:
				acl.ace_inheritedobjecttype = str(t)
				
			true_attr, false_attr = NetDACL.mask2attr(ace.Mask)
			
			for attr in true_attr:	
				setattr(acl, attr, True)
			for attr in false_attr:	
				setattr(acl, attr, False)
				
			true_attr, false_attr = NetDACL.hdrflag2attr(ace.Header.AceFlags)
			
			for attr in true_attr:	
				setattr(acl, attr, True)
			for attr in false_attr:	
				setattr(acl, attr, False)
			
			acl.ace_sid = str(ace.Sid)
			self.db_session.add(acl)
		
		self.db_session.commit()

	def run(self):
		self.setup()
		try:
			self.collect_results()
		except:
			print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
			traceback.print_exc()

	def collect_results(self):
		while True:
			result = self.out_q.get()
			if result is None:
				#print('enumerator finished!')
				break

			if isinstance(result, SMBEnumError):
				#something went error
				tid = result.settings
				if result.settings is not None:
					tid = result.settings.target
				logger.debug('[AIOSMBShareGatherer][Error][%s] %s' % (tid, result.error))
				if self.use_progress_bar is True:
					self.prg_errors.update()

			elif isinstance(result, SMBShareGathererResult):
				if result.type == 'dir':
					if self.use_progress_bar is True:
						self.prg_dirs.update()

					
					nd = NetDir()
					nd.share_id = result.settings.share_id
					nd.parent_id = self.get_dir_id(result.result.unc_path, result.result.name)
					nd.creation_time = result.result.creation_time
					nd.last_access_time = result.result.creation_time
					nd.last_write_time = result.result.last_write_time
					nd.change_time = result.result.change_time
					nd.unc = result.result.unc_path
					nd.name = result.result.name
					self.db_session.add(nd)
					self.db_session.commit()
					self.db_session.refresh(nd)
					self.dir_lookup[result.result.unc_path] = nd.id
					for subdir in result.result.subdirs:
						sd = result.result.subdirs[subdir]
						nsd = NetDir()
						nsd.share_id = result.settings.share_id
						nsd.parent_id = nd.id
						nsd.creation_time = sd.creation_time
						nsd.last_access_time = sd.creation_time
						nsd.last_write_time = sd.last_write_time
						nsd.change_time = sd.change_time
						nsd.unc = sd.unc_path
						nsd.name = sd.name
						self.db_session.add(nsd)
						self.db_session.commit()
						self.db_session.refresh(nsd)
						self.dir_lookup[sd.unc_path] = nd.id
						self.store_sd(sd.sid, 'dir', nd.id)

					for filename in result.result.files:
						if self.use_progress_bar is True:
							self.prg_files.update()
						f = result.result.files[filename]
						nf = NetFile()
						nf.folder_id = nd.id
						nf.creation_time = f.creation_time
						nf.last_access_time = f.last_access_time
						nf.last_write_time = f.last_write_time
						nf.change_time = f.change_time
						nf.unc = f.unc_path
						nf.size = f.size
						name = f.name
						x = f.name.rsplit('.',1)
						if len(x) > 1:
							name = x[0]
							ext = x[1]
						nf.name = name
						nf.ext = ext
						self.db_session.add(nf)
						self.db_session.commit()
						self.db_session.refresh(nf)
						self.store_sd(f.sid, 'file', nf.id)

				#elif result.type == 'file':
					

			#if result is None and error is None:
			#	logger.debug('Finished: %s' % target.ip)
			#	if self.use_progress_bar is True:
			#		self.prg_hosts.update()


if __name__ == '__main__':
	db_conn = 'sqlite:///a.db'
	create_db(db_conn)
	smb_mgr = SMBConnectionURL('smb+ntlm-password://TEST\\victim:Passw0rd!1@10.10.10.2')	
	
	ad_id = 0
	settings = SMBShareGathererSettings(ad_id, smb_mgr, None, None, None)
	ep = ShareGathererManager(settings, db_conn = db_conn, worker_cnt = 30)
	ep.run()
	print('done!')