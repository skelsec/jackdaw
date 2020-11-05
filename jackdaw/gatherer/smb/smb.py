#!/usr/bin/env python3
#
# Author:
#  Tamas Jos (@skelsec)
#

import os
import asyncio
import logging
import json
import traceback
import ipaddress

from tqdm import tqdm

from jackdaw import logger
from jackdaw.dbmodel import get_session, windowed_query
from jackdaw.dbmodel.netshare import NetShare
from jackdaw.dbmodel.netsession import NetSession
from jackdaw.dbmodel.localgroup import LocalGroup
from jackdaw.dbmodel.smbfinger import SMBFinger
from jackdaw.dbmodel.adinfo import ADInfo
from jackdaw.dbmodel.adcomp import Machine
from jackdaw.dbmodel.neterror import NetError

from jackdaw.common.cpucount import get_cpu_count
from jackdaw.gatherer.smb.agent.agent import AIOSMBGathererAgent
from jackdaw.gatherer.progress import *

import aiosmb
from aiosmb.commons.utils.extb import format_exc
from sqlalchemy import func

class SMBGatherer:
	def __init__(self, db_conn, ad_id, smb_mgr, worker_cnt = None, progress_queue = None, show_progress = True, stream_data = False):
		self.in_q = None
		self.out_q = None
		self.smb_mgr = smb_mgr
		self.gathering_type = ['all']
		self.localgroups = ['Administrators', 'Distributed COM Users','Remote Desktop Users','Remote Management Users']
		self.concurrent_connections = worker_cnt if worker_cnt is not None else get_cpu_count()
		self.db_conn = db_conn
		self.progress_queue = progress_queue
		self.show_progress = show_progress

		self.queue_size = self.concurrent_connections

		self.total_targets = 0
		self.session = None

		self.gatherer = None
		self.gatherer_task = None
		self.job_generator_task = None
		self.domain_name = None
		self.ad_id = ad_id

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
		self.progress_step_size = 1

		self.results_thread = None
		self.stream_data = stream_data

	async def terminate(self):
		if self.job_generator_task is not None:
			self.job_generator_task.cancel()
		
		if self.gatherer_task is not None:
			await self.gatherer.terminate()
			self.gatherer_task.cancel()
			
	async def generate_targets(self):
		try:
			q = self.session.query(Machine).filter_by(ad_id = self.ad_id)
			for machine in windowed_query(q, Machine.id, 100):
				try:
					dns_name = machine.dNSHostName
					if dns_name is None or dns_name == '':
						dns_name = '%s.%s' % (str(machine.sAMAccountName[:-1]), str(self.domain_name))
					await self.in_q.put((machine.objectSid, dns_name))
				except:
					continue

			#signaling the ed of target generation
			await self.in_q.put(None)
		except Exception as e:
			logger.exception('smb generate_targets')
		
	async def run(self):
		try:
			logger.debug('[+] Starting SMB information acqusition. This might take a while...')
			self.session = get_session(self.db_conn)
			self.in_q = asyncio.Queue(self.queue_size)
			self.out_q = asyncio.Queue(self.queue_size)
			
			
			
			info = self.session.query(ADInfo).get(self.ad_id)
			info.smb_enumeration_state = 'STARTED'
			self.domain_name = str(info.distinguishedName).replace(',','.').replace('DC=','')
			self.session.commit()
			
			self.total_targets = self.session.query(func.count(Machine.id)).filter(Machine.ad_id == self.ad_id).scalar()
			
			
			if self.show_progress is True:
				self.prg_hosts = tqdm(desc='HOSTS', ascii = True, total = self.total_targets)
				self.prg_shares = tqdm(desc='Shares', ascii = True)
				self.prg_sessions = tqdm(desc='Sessions', ascii = True)
				self.prg_groups = tqdm(desc='LocalGroup', ascii = True)
				self.prg_errors = tqdm(desc='Errors', ascii = True)
			
			if self.progress_queue is not None:
				msg = GathererProgress()
				msg.type = GathererProgressType.SMB
				msg.msg_type = MSGTYPE.STARTED
				msg.adid = self.ad_id
				msg.domain_name = self.domain_name
				await self.progress_queue.put(msg)

			self.gatherer = AIOSMBGathererAgent(
				self.in_q, 
				self.out_q, 
				self.smb_mgr, 
				gather = self.gathering_type, 
				localgroups = self.localgroups, 
				concurrent_connections = self.concurrent_connections,
			)
			self.gatherer_task = asyncio.create_task(self.gatherer.run())
			self.job_generator_task = asyncio.create_task(self.generate_targets())
			
			while True:
				await asyncio.sleep(0)
				x = await self.out_q.get()
				if x is None:
					break

				tid, target, result, error = x
				if result is None and error is not None:
					#something went error
					if tid is None and target is None:
						continue
					logger.debug('[AIOSMBScanner][TargetError][%s] %s' % (target.get_ip(), error))
					if self.show_progress is True:
						self.prg_errors.update()
					if self.progress_queue is not None:
						self.prg_errors_cnt += 1
					
					err = NetError()
					err.ad_id = self.ad_id
					err.machine_sid = tid
					err.error = str(error)
					self.session.add(err)
					

				if result is not None:
					if self.show_progress is True:
						if isinstance(result, NetSession):
							self.prg_sessions.update()
						elif isinstance(result, NetShare):
							self.prg_shares.update()
						elif isinstance(result, LocalGroup):
							self.prg_groups.update()
					
					if self.progress_queue is not None:
						if isinstance(result, NetSession):
							self.prg_sessions_cnt += 1
							if self.stream_data is True:
								msg = GathererProgress()
								msg.type = GathererProgressType.SMBSESSION
								msg.msg_type = MSGTYPE.FINISHED
								msg.adid = self.ad_id
								msg.domain_name = self.domain_name
								msg.data = result
								await self.progress_queue.put(msg)

						elif isinstance(result, NetShare):
							self.prg_shares_cnt += 1
							if self.stream_data is True:
								msg = GathererProgress()
								msg.type = GathererProgressType.SMBSHARE
								msg.msg_type = MSGTYPE.FINISHED
								msg.adid = self.ad_id
								msg.domain_name = self.domain_name
								msg.data = result
								await self.progress_queue.put(msg)
								
						elif isinstance(result, LocalGroup):
							self.prg_groups_cnt += 1
							if self.stream_data is True:
								msg = GathererProgress()
								msg.type = GathererProgressType.SMBLOCALGROUP
								msg.msg_type = MSGTYPE.FINISHED
								msg.adid = self.ad_id
								msg.domain_name = self.domain_name
								msg.data = result
								await self.progress_queue.put(msg)

					result.ad_id = self.ad_id
					self.session.add(result)
					self.session.commit()

				if result is None and error is None:
					logger.debug('Finished: %s' % target.ip)
					if self.show_progress is True:
						self.prg_hosts.update()
					
					if self.progress_queue is not None:
						self.prg_hosts_cnt += 1
						if self.prg_hosts_cnt % self.progress_step_size == 0:
							msg = GathererProgress()
							msg.type = GathererProgressType.SMB
							msg.msg_type = MSGTYPE.PROGRESS 
							msg.adid = self.ad_id
							msg.domain_name = self.domain_name
							msg.errors = self.prg_errors_cnt
							msg.sessions = self.prg_sessions_cnt
							msg.shares = self.prg_shares_cnt
							msg.groups = self.prg_groups_cnt
							msg.total = self.total_targets
							msg.total_finished = self.prg_hosts_cnt
							msg.step_size = self.progress_step_size

							await self.progress_queue.put(msg)

			info = self.session.query(ADInfo).get(self.ad_id)
			info.smb_enumeration_state = 'FINISHED'
			self.session.commit()

			logger.debug('[+] SMB information acquisition finished!')
			if self.progress_queue is not None:
				msg = GathererProgress()
				msg.type = GathererProgressType.SMB
				msg.msg_type = MSGTYPE.FINISHED
				msg.adid = self.ad_id
				msg.domain_name = self.domain_name
				await self.progress_queue.put(msg)

			if self.show_progress is True:
				self.prg_hosts.refresh()
				self.prg_shares.refresh()
				self.prg_sessions.refresh()
				self.prg_groups.refresh()
				self.prg_errors.refresh()
				self.prg_hosts.disable = True
				self.prg_shares.disable = True
				self.prg_sessions.disable = True
				self.prg_groups.disable = True
				self.prg_errors.disable = True
			return True, None
		except Exception as e:
			return False, e

