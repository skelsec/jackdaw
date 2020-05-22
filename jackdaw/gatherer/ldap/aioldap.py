#!/usr/bin/env python3
#
# Author:
#  Tamas Jos (@skelsec)
#

import os
import re
import enum
import gzip
import base64
import asyncio
import datetime
import threading
import traceback
import multiprocessing
from hashlib import sha1

from sqlalchemy import func

from jackdaw.dbmodel.graphinfo import JackDawGraphInfo
from jackdaw.dbmodel.spnservice import JackDawSPNService
from jackdaw.dbmodel.addacl import JackDawADDACL
from jackdaw.dbmodel.adgroup import JackDawADGroup
from jackdaw.dbmodel.adinfo import JackDawADInfo
from jackdaw.dbmodel.aduser import JackDawADUser
from jackdaw.dbmodel.adcomp import JackDawADMachine
from jackdaw.dbmodel.adou import JackDawADOU
from jackdaw.dbmodel.adinfo import JackDawADInfo
from jackdaw.dbmodel.adgpo import JackDawADGPO
from jackdaw.dbmodel.constrained import JackDawMachineConstrainedDelegation, JackDawUserConstrainedDelegation
from jackdaw.dbmodel.adgplink import JackDawADGplink
from jackdaw.dbmodel.adsd import JackDawSD
from jackdaw.dbmodel.adtrust import JackDawADTrust
from jackdaw.dbmodel.adspn import JackDawSPN
from jackdaw.dbmodel import get_session
from jackdaw.dbmodel.edge import JackDawEdge
from jackdaw.dbmodel.edgelookup import JackDawEdgeLookup
from jackdaw.wintypes.lookup_tables import *
from jackdaw import logger

from jackdaw.common.apq import AsyncProcessQueue

from msldap.ldap_objects import *
from winacl.dtyp.security_descriptor import SECURITY_DESCRIPTOR
from tqdm import tqdm

from jackdaw.gatherer.ldap.progress import LDAPGathererProgress
from jackdaw.gatherer.ldap.agent.common import *
from jackdaw.gatherer.ldap.agent.agent import LDAPGathererAgent
from jackdaw.gatherer.ldap.collectors.base import BaseCollector
from jackdaw.gatherer.ldap.collectors.sd import SDCollector
from jackdaw.gatherer.ldap.collectors.membership import MembershipCollector
import pathlib

class LDAPGatherer:
	def __init__(self, db_conn, ldap_mgr, agent_cnt = None, progress_queue = None, ad_id = None, graph_id = None, work_dir = None, show_progress = True):
		self.db_conn = db_conn
		self.ldap_mgr = ldap_mgr
		self.work_dir = work_dir
		self.show_progress = show_progress

		self.progress_queue = progress_queue
		self.session = None

		self.agent_in_q = None
		self.agent_out_q = None
		self.agents = []

		self.agent_cnt = agent_cnt
		if agent_cnt is None:
			self.agent_cnt = min(multiprocessing.cpu_count(), 3)
		
		self.graph_id = graph_id
		self.resumption = False
		self.ad_id = ad_id
		if ad_id is not None:
			self.resumption = True
		self.domain_name = None

		self.members_target_file_name = None
		self.sd_target_file_name = None

	async def restart_agents(self):
		try:
			print('Stopping initial agents')
			for agent in self.agents:
				await self.agent_in_q.put(None)

			for agent in self.agents:
				agent.cancel()

			print('Resetting queues and restarting agents')
			self.agent_in_q = asyncio.Queue(self.agent_cnt)
			self.agent_out_q = asyncio.Queue(self.agent_cnt)
			print(self.agent_cnt)
			for _ in range(1):
				agent = LDAPGathererAgent(self.ldam_mgr, self.agent_in_q, self.agent_out_q)
				self.agents.append(asyncio.create_task(agent.arun()))
		except Exception as e:
			logger.exception('restart agents')

	async def run(self):
		try:
			logger.info('[+] Starting LDAP information acqusition. This might take a while...')
			self.session = get_session(self.db_conn)

			if self.work_dir is None:
				self.work_dir = pathlib.Path('./workdir')
				self.work_dir.mkdir(parents=True, exist_ok=True)
			if isinstance(self.work_dir, str) is True:
				self.work_dir = pathlib.Path(self.work_dir)
			
			self.members_target_file_name = str(self.work_dir.joinpath('temp_members_list.gz'))
			self.sd_target_file_name = (self.work_dir.joinpath('temp_sd_list.gz'))

			self.members_file_handle = gzip.GzipFile(self.members_target_file_name,mode='wb')
			self.sd_file_handle = gzip.GzipFile(self.sd_target_file_name,mode='wb')

			if self.resumption is False:
				bc = BaseCollector(
					self.session, 
					self.ldap_mgr, 
					agent_cnt = self.agent_cnt, 
					progress_queue = self.progress_queue, 
					show_progress = self.show_progress,
					members_file_handle = self.members_file_handle,
					sd_file_handle = self.sd_file_handle
				)
				self.ad_id, self.graph_id, err = await bc.run()
				if err is False:
					return None, None, err

			self.members_file_handle.close()
			self.sd_file_handle.close()
			self.members_file_handle = gzip.GzipFile(self.members_target_file_name,mode='rb')
			self.sd_file_handle = gzip.GzipFile(self.sd_target_file_name,mode='rb')


			sdc = SDCollector(
				self.session, 
				self.ldap_mgr, 
				ad_id = self.ad_id, 
				graph_id = self.graph_id, 
				agent_cnt = self.agent_cnt, 
				sd_target_file_handle = self.sd_file_handle, 
				resumption = self.resumption, 
				progress_queue = self.progress_queue, 
				show_progress = self.show_progress
			)
			_, err = await sdc.run()
			if err is not None:
				raise err

			mc = MembershipCollector(
				self.session,
				self.ldap_mgr,
				ad_id = self.ad_id,
				agent_cnt = self.agent_cnt,
				resumption = False,
				progress_queue = self.progress_queue,
				show_progress = self.show_progress,
				graph_id = None,
				members_target_file_handle = self.members_file_handle
			)
			_, err = await mc.run()
			if err is not None:
				raise err


			logger.info('[+] LDAP information acqusition finished!')
			return self.ad_id, self.graph_id, None
		except Exception as e:
			return None, None, e

		finally:
			if self.members_target_file_name is not None:
				if self.members_file_handle is not None:
					try:
						self.members_file_handle.close()
					except:
						pass
				try:
					os.unlink(self.members_target_file_name)
				except:
					pass
			if self.sd_target_file_name is not None:
				if self.sd_file_handle is not None:
					try:
						self.sd_file_handle.close()
					except:
						pass
				try:
					os.unlink(self.sd_target_file_name)
				except:
					pass
			

if __name__ == '__main__':
	from msldap.commons.url import MSLDAPURLDecoder

	import sys
	sql = sys.argv[1]
	ldap_conn_url = sys.argv[2]

	print(sql)
	print(ldap_conn_url)
	logger.setLevel(2)

	ldap_mgr = MSLDAPURLDecoder(ldap_conn_url)

	mgr = LDAPEnumeratorManager(sql, ldap_mgr)
	mgr.run()