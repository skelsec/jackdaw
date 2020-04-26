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

class SMBGathererManager:
	def __init__(self, smb_mgr, worker_cnt = 50, queue_size = 100000):
		self.queue_size = queue_size
		self.in_q = AsyncProcessQueue(queue_size)
		self.out_q = AsyncProcessQueue(queue_size)
		self.smb_mgr = smb_mgr
		self.gathering_type = ['all']
		self.localgroups = ['Administrators', 'Distributed COM Users','Remote Desktop Users']
		self.concurrent_connections = worker_cnt
		self.domain = None
		self.dc_ip = None
		self.timeout = 3
		self.db_conn = None

		self.total_targets = 0
		self.targets = []
		self.targets_file = None
		self.ldap_conn = None
		self.target_ad = None
		self.lookup_ad = None #if specified, it will look up the targets in the DB.
		self.out_file = None

		self.gatherer = None
		
		self.use_progress_bar = True
		self.prg_hosts = None
		self.prg_shares = None
		self.prg_sessions = None
		self.prg_groups = None
		self.prg_errors = None

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
			for target_id, target_name in session.query(JackDawADMachine).filter_by(ad_id = self.target_ad).with_entities(JackDawADMachine.id, JackDawADMachine.sAMAccountName):
				yield (target_id, target_name[:-1])

		if self.db_conn is not None:
			session.close()

	def get_results(self):
		session = None
		if self.db_conn is not None:
			session = get_session(self.db_conn)
		
		while True:
			x = self.out_q.get()
			if x is None:
				break

			tid, target, result, error = x
			if result is None and error is not None:
				#something went error
				logger.debug('[AIOSMBScanner][TargetError][%s] %s' % (target.get_ip(), error))
				if self.use_progress_bar is True:
					self.prg_errors.update()

			if result is not None:
				if self.use_progress_bar is True:
					if isinstance(result, NetSession):
						self.prg_sessions.update()
					elif isinstance(result, NetShare):
						self.prg_shares.update()
					elif isinstance(result, LocalGroup):
						self.prg_groups.update()

				if session is None:
					logger.debug(target, str(result), error)
				else:
					session.add(result)
					session.commit()

			if result is None and error is None:
				logger.debug('Finished: %s' % target.ip)
				if self.use_progress_bar is True:
					self.prg_hosts.update()
	
	def run(self):
		logger.info('[+] Starting SMB information acqusition. This might take a while...')
		self.in_q = AsyncProcessQueue()
		self.out_q = AsyncProcessQueue()
		if self.use_progress_bar is True:
			self.prg_hosts = tqdm(desc='HOSTS', ascii = True)
			self.prg_shares = tqdm(desc='Shares', ascii = True)
			self.prg_sessions = tqdm(desc='Sessions', ascii = True)
			self.prg_groups = tqdm(desc='LocalGroup', ascii = True)
			self.prg_errors = tqdm(desc='Errors', ascii = True)

		self.results_thread = threading.Thread(target = self.get_results)
		self.results_thread.daemon = True
		self.results_thread.start()

		self.gatherer = AIOSMBGatherer(self.in_q, self.out_q, self.smb_mgr, gather = self.gathering_type, localgroups = self.localgroups, concurrent_connections = self.concurrent_connections)
		self.gatherer.start()
		
		for target in self.__target_generator():
			self.total_targets += 1
			if self.use_progress_bar is True:
				self.prg_hosts.total = self.total_targets
			self.in_q.put(target)
		
		self.in_q.put(None)
		#if self.use_progress_bar is True:
		#	self.prg_hosts.total = self.total_targets

		self.results_thread.join()
		logger.info('[+] SMB information acqusition finished!')


class AIOSMBGatherer(multiprocessing.Process):
	def __init__(self, in_q, out_q, smb_mgr, gather = ['all'], localgroups = [], concurrent_connections = 10):
		multiprocessing.Process.__init__(self)
		self.in_q = in_q
		self.out_q = out_q
		self.smb_mgr = smb_mgr
		self.gather = gather
		self.localgroups = localgroups
		self.concurrent_connections = concurrent_connections

		self.targets = []
		self.worker_q = None

	def setup(self):
		pass

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
						await self.out_q.coro_put((tid, connection.target, f, None))
					except:
						traceback.print_exc()

				machine = SMBMachine(connection)


				if 'all' in self.gather or 'shares' in self.gather:
					async for smbshare, err in machine.list_shares():
						if err is not None:
							await self.out_q.coro_put((tid, connection.target, None, 'Failed to list shares. Reason: %s' % format_exc(err)))
							continue
						share = NetShare()
						share.machine_id = tid
						share.ip = connection.target.get_ip()
						share.netname = smbshare.name
						share.type = smbshare.type
						share.remark = smbshare.remark

						await self.out_q.coro_put((tid, connection.target, share, None))
					
				
				if 'all' in self.gather or 'sessions' in self.gather:
					async for session, err in machine.list_sessions():
						if err is not None:
							await self.out_q.coro_put((tid, connection.target, None, 'Failed to get sessions. Reason: %s' % format_exc(err)))
							continue

						sess = NetSession()
						sess.machine_id = tid
						sess.source = connection.target.get_ip()
						sess.ip = session.ip_addr.replace('\\','').strip()
						sess.username = session.username

						await self.out_q.coro_put((tid, connection.target, sess, None))

				if 'all' in self.gather or 'localgroups' in self.gather:
					for group_name in self.localgroups:
						async for domain_name, user_name, sid, err in machine.list_group_members('Builtin', group_name):
							if err is not None:
								await self.out_q.coro_put((tid, connection.target, None, 'Failed to connect to poll group memeberships. Reason: %s' % format_exc(err)))
								continue

							lg = LocalGroup()
							lg.machine_id = tid
							lg.ip = connection.target.get_ip()
							lg.hostname = connection.target.get_hostname()
							lg.sid = sid
							lg.groupname = group_name
							lg.domain = domain_name
							lg.username = user_name
							await self.out_q.coro_put((tid, connection.target, lg, None))
		
		except Exception as e:
			await self.out_q.coro_put((tid, connection.target, None, 'Failed to connect to host. Reason: %s' % format_exc(e)))
			return

		finally:
			await self.out_q.coro_put((tid, connection.target, None, None)) #target finished

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
			except Exception as e:
				logger.exception('WORKER ERROR')
				raise

	async def scan_queue(self):
		"""
		Reads targets from queue and scans them
		"""
		self.worker_q = asyncio.Queue()
		tasks = []
		for _ in range(self.concurrent_connections):
			tasks.append(asyncio.create_task(self.worker()))

		while True:
			target = await self.in_q.coro_get()
			if target is None:
				for _ in range(self.concurrent_connections):
					await self.worker_q.put(None)
				break
			else:
				await self.worker_q.put(target)

		results = await asyncio.gather(*tasks, return_exceptions = True)
		for res in results:
			if isinstance(res, Exception):
				logger.error('Error! %s' % res)
		await self.out_q.coro_put(None)
		

	
	def run(self):
		self.setup()
		try:
			loop = asyncio.get_event_loop()
		except:
			loop = asyncio.new_event_loop()
		#loop.set_debug(True)  # Enable debug
		loop.run_until_complete(self.scan_queue())


