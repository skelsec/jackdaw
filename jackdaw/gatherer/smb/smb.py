#!/usr/bin/env python3
#
# Author:
#  Tamas Jos (@skelsec)
#

import asyncio
import logging
import json
import traceback
import ipaddress
import multiprocessing
import threading

from tqdm import tqdm
from dns import resolver, reversename

import aiosmb
from aiosmb.commons.interfaces.machine import SMBMachine
from aiosmb.commons.utils.extb import format_exc

from jackdaw.common.apq import AsyncProcessQueue
from jackdaw.dbmodel.netshare import NetShare
from jackdaw.dbmodel.netsession import NetSession
from jackdaw.dbmodel.localgroup import LocalGroup
from jackdaw.dbmodel.smbfinger import SMBFinger
from jackdaw import logger
from jackdaw.dbmodel import get_session

from jackdaw.dbmodel.adinfo import JackDawADInfo
from jackdaw.dbmodel.adcomp import JackDawADMachine

class SMBEnumeratorProgress:
	def __init__(self):
		self.type = 'SMB'
		self.msg_type = 'PROGRESS'
		self.adid = None
		self.domain_name = None
		self.errors = None
		self.sessions = None
		self.shares = None
		self.groups = None
		self.hosts = None

	def __str__(self):
		if self.msg_type == 'PROGRESS':
			return '[%s][%s][%s][%s] HOSTS %s SHARES %s SESSIONS %s GROUPS %s ERRORS %s' % (
				self.type, 
				self.domain_name, 
				self.adid,
				self.msg_type,
				self.hosts, 
				self.shares, 
				self.sessions, 
				self.groups, 
				self.errors
			
			)
		
		return '[%s][%s][%s][%s]' % (self.type, self.domain_name, self.adid, self.msg_type)

class SMBGathererManager:
	def __init__(self, smb_mgr, worker_cnt = 50, queue_size = 100000, progress_queue = None):
		self.queue_size = queue_size
		self.in_q = None
		self.out_q = None
		self.smb_mgr = smb_mgr
		self.gathering_type = ['all']
		self.localgroups = ['Administrators', 'Distributed COM Users','Remote Desktop Users']
		self.concurrent_connections = worker_cnt if worker_cnt is not None else multiprocessing.cpu_count()
		self.db_conn = None
		self.progress_queue = progress_queue

		self.total_targets = 0
		self.targets = []
		self.targets_file = None
		self.ldap_conn = None
		self.target_ad = None
		self.lookup_ad = None #if specified, it will look up the targets in the DB.
		self.out_file = None

		self.gatherer = None
		self.gatherer_task = None
		self.job_generator_task = None
		self.domain_name = None
		
		self.prg_hosts = None
		self.prg_shares = None
		self.prg_sessions = None
		self.prg_groups = None
		self.prg_errors = None

		self.prg_errors_cnt = 0
		self.prg_sessions_cnt = 0
		self.prg_shares_cnt = 0
		self.prg_groups_cnt = 0
		self.prg_hosts_cnt = 0

		self.results_thread = None

	def __target_generator(self):
		if self.db_conn is not None:
			session = get_session(self.db_conn)
		
		for target in self.targets:
			tid = -1
			yield (tid, target)

		if self.targets_file is not None:
			tid = -1
			with open(self.targets_file, 'r') as f:
				for line in f:
					line = line.strip()
					yield (tid, line)

		if self.ldap_conn is not None:
			ldap_filter = r'(&(sAMAccountType=805306369))'
			attributes = ['sAMAccountName']
			for entry in self.ldap_conn.pagedsearch(ldap_filter, attributes):
				tid = -1
				if self.lookup_ad is not None:
					res = session.query(JackDawADMachine)\
							.filter_by(ad_id = self.lookup_ad)\
							.with_entities(JackDawADMachine.id)\
							.filter(JackDawADMachine.sAMAccountName == entry['attributes']['sAMAccountName'])\
							.first()
					if res is not None:
						tid = res[0]
				
				yield (tid, entry['attributes']['sAMAccountName'][:-1])

		if self.target_ad is not None:
			info = session.query(JackDawADInfo).get(self.target_ad)
			info.smb_enumeration_state = 'STARTED'
			self.domain_name = str(info.distinguishedName).replace(',','.').replace('DC=','')
			session.commit()
			for target_id, target_name in session.query(JackDawADMachine).filter_by(ad_id = self.target_ad).with_entities(JackDawADMachine.id, JackDawADMachine.sAMAccountName):
				yield (target_id, target_name[:-1])

		if self.db_conn is not None:
			session.close()

	async def terminate(self):
		if self.job_generator_task is not None:
			self.job_generator_task.cancel()
		
		if self.gatherer_task is not None:
			await self.gatherer.terminate()
			self.gatherer_task.cancel()
			
	async def generate_targets(self):
		for target in self.__target_generator():
			self.total_targets += 1
			if self.progress_queue is None:
				self.prg_hosts.total = self.total_targets
			await self.in_q.put(target)
		
		await self.in_q.put(None)
	
	async def run(self):
		logger.info('[+] Starting SMB information acqusition. This might take a while...')
		self.in_q = asyncio.Queue(self.queue_size)
		self.out_q = asyncio.Queue(self.queue_size)
		if self.progress_queue is None:
			self.prg_hosts = tqdm(desc='HOSTS', ascii = True)
			self.prg_shares = tqdm(desc='Shares', ascii = True)
			self.prg_sessions = tqdm(desc='Sessions', ascii = True)
			self.prg_groups = tqdm(desc='LocalGroup', ascii = True)
			self.prg_errors = tqdm(desc='Errors', ascii = True)
		
		else:
			msg = SMBEnumeratorProgress()
			msg.msg_type = 'STARTED'
			msg.adid = self.target_ad
			msg.domain_name = self.domain_name
			await self.progress_queue.put(msg)

		#self.results_thread = threading.Thread(target = self.get_results)
		#self.results_thread.daemon = True
		#self.results_thread.start()

		self.gatherer = AIOSMBGatherer(
			self.in_q, 
			self.out_q, 
			self.smb_mgr, 
			gather = self.gathering_type, 
			localgroups = self.localgroups, 
			concurrent_connections = self.concurrent_connections,
			progress_queue = self.progress_queue
		)
		self.gatherer_task = asyncio.create_task(self.gatherer.run())
		
		self.job_generator_task = asyncio.create_task(self.generate_targets())
		
		session = None
		if self.db_conn is not None:
			session = get_session(self.db_conn)
		
		while True:
			x = await self.out_q.get()
			if x is None:
				break

			tid, target, result, error = x
			if result is None and error is not None:
				#something went error
				logger.debug('[AIOSMBScanner][TargetError][%s] %s' % (target.get_ip(), error))
				if self.progress_queue is None:
					self.prg_errors.update()
				else:
					self.prg_errors_cnt += 1

			if result is not None:
				if self.progress_queue is None:
					if isinstance(result, NetSession):
						self.prg_sessions.update()
					elif isinstance(result, NetShare):
						self.prg_shares.update()
					elif isinstance(result, LocalGroup):
						self.prg_groups.update()
				
				else:
					if isinstance(result, NetSession):
						self.prg_sessions_cnt += 1
					elif isinstance(result, NetShare):
						self.prg_shares_cnt += 1
					elif isinstance(result, LocalGroup):
						self.prg_groups_cnt += 1

				if session is None:
					logger.debug(target, str(result), error)
				else:
					session.add(result)
					session.commit()

			if result is None and error is None:
				logger.debug('Finished: %s' % target.ip)
				if self.progress_queue is None:
					self.prg_hosts.update()
				else:
					self.prg_hosts_cnt += 1
					msg = SMBEnumeratorProgress()
					msg.adid = self.target_ad
					msg.domain_name = self.domain_name
					msg.errors = self.prg_errors_cnt
					msg.sessions = self.prg_sessions_cnt
					msg.shares = self.prg_shares_cnt
					msg.groups = self.prg_groups_cnt
					msg.hosts = self.prg_hosts_cnt

					await self.progress_queue.put(msg)

		
		logger.info('[+] SMB information acqusition finished!')
		if self.progress_queue is not None:
			msg = SMBEnumeratorProgress()
			msg.msg_type = 'FINISHED'
			msg.adid = self.target_ad
			msg.domain_name = self.domain_name
			await self.progress_queue.put(msg)

		if session is not None and self.target_ad is not None:
			info = session.query(JackDawADInfo).get(self.target_ad)
			info.smb_enumeration_state = 'FINISHED'
			session.commit()


class AIOSMBGatherer:
	def __init__(self, in_q, out_q, smb_mgr, gather = ['all'], localgroups = [], concurrent_connections = 10, progress_queue = None):
		#multiprocessing.Process.__init__(self)
		self.in_q = in_q
		self.out_q = out_q
		self.smb_mgr = smb_mgr
		self.gather = gather
		self.localgroups = localgroups
		self.concurrent_connections = concurrent_connections
		self.progress_queue = progress_queue

		self.worker_tasks = []
		self.targets = []
		self.worker_q = None

	async def scan_host(self, atarget):
		try:
			tid, target = atarget
			#spneg = AuthenticatorBuilder.to_spnego_cred(self.credential, target)
			connection = self.smb_mgr.create_connection_newtarget(target)
			async with connection:
				await connection.login()
				
				extra_info = connection.get_extra_info()
				if extra_info is not None:
					try:
						f = SMBFinger.from_extra_info(tid, extra_info)
						await self.out_q.put((tid, connection.target, f, None))
					except:
						traceback.print_exc()

				machine = SMBMachine(connection)


				if 'all' in self.gather or 'shares' in self.gather:
					async for smbshare, err in machine.list_shares():
						if err is not None:
							await self.out_q.put((tid, connection.target, None, 'Failed to list shares. Reason: %s' % format_exc(err)))
							continue
						share = NetShare()
						share.machine_id = tid
						share.ip = connection.target.get_ip()
						share.netname = smbshare.name
						share.type = smbshare.type
						share.remark = smbshare.remark

						await self.out_q.put((tid, connection.target, share, None))
					
				
				if 'all' in self.gather or 'sessions' in self.gather:
					async for session, err in machine.list_sessions():
						if err is not None:
							await self.out_q.put((tid, connection.target, None, 'Failed to get sessions. Reason: %s' % format_exc(err)))
							continue

						sess = NetSession()
						sess.machine_id = tid
						sess.source = connection.target.get_ip()
						sess.ip = session.ip_addr.replace('\\','').strip()
						sess.username = session.username

						await self.out_q.put((tid, connection.target, sess, None))

				if 'all' in self.gather or 'localgroups' in self.gather:
					for group_name in self.localgroups:
						async for domain_name, user_name, sid, err in machine.list_group_members('Builtin', group_name):
							if err is not None:
								await self.out_q.put((tid, connection.target, None, 'Failed to connect to poll group memeberships. Reason: %s' % format_exc(err)))
								continue

							lg = LocalGroup()
							lg.machine_id = tid
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
		while True:
			try:
				target = await self.worker_q.get()
				if target is None:
					return
				try:
					await self.scan_host(target)
				except:
					#exception should be handled in scan_host
					continue
			except asyncio.CancelledError:
				return
			except Exception as e:
				logger.exception('WORKER ERROR')
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
					logger.error('Error! %s' % res)
			await self.out_q.put(None)
		except:
			import traceback
			traceback.print_exc()


