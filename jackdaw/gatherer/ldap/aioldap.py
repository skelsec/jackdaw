#!/usr/bin/env python3
#
# Author:
#  Tamas Jos (@skelsec)
#

import os
import re
import enum
import gzip
import json
import base64
import asyncio
import datetime
import traceback
from hashlib import sha1

from sqlalchemy import func

#from jackdaw.dbmodel.addacl import JackDawADDACL
from jackdaw.dbmodel.spnservice import SPNService
from jackdaw.dbmodel.adgroup import Group
from jackdaw.dbmodel.adinfo import ADInfo
from jackdaw.dbmodel.aduser import ADUser
from jackdaw.dbmodel.adcomp import Machine
from jackdaw.dbmodel.adou import ADOU
from jackdaw.dbmodel.adinfo import ADInfo
from jackdaw.dbmodel.adgpo import GPO
from jackdaw.dbmodel.constrained import MachineConstrainedDelegation
from jackdaw.dbmodel.adgplink import Gplink
from jackdaw.dbmodel.adsd import JackDawSD
from jackdaw.dbmodel.adtrust import ADTrust
from jackdaw.dbmodel.adspn import JackDawSPN
from jackdaw.dbmodel import get_session
from jackdaw.dbmodel.edge import Edge
from jackdaw.dbmodel.edgelookup import EdgeLookup
from jackdaw.dbmodel import windowed_query
from jackdaw.wintypes.lookup_tables import *
from jackdaw import logger

from msldap.ldap_objects import *
from winacl.dtyp.security_descriptor import SECURITY_DESCRIPTOR
from tqdm import tqdm

from jackdaw.common.cpucount import get_cpu_count
from jackdaw.gatherer.progress import *
from jackdaw.gatherer.ldap.agent.common import *
from jackdaw.gatherer.ldap.agent.agent import LDAPGathererAgent
from jackdaw.gatherer.ldap.collectors.base import BaseCollector
from jackdaw.gatherer.ldap.collectors.sd import SDCollector
from jackdaw.gatherer.ldap.collectors.membership import MembershipCollector
import pathlib

class LDAPGatherer:
	def __init__(self, db_conn, ldap_mgr, agent_cnt = None, progress_queue = None, ad_id = None, graph_id = None, work_dir = None, show_progress = True, store_to_db = True, base_collection_finish_evt = None, stream_data = False, no_work_dir = False):
		self.db_conn = db_conn
		self.ldap_mgr = ldap_mgr
		self.work_dir = work_dir
		self.no_work_dir = no_work_dir
		self.show_progress = show_progress
		self.store_to_db = store_to_db
		self.progress_queue = progress_queue
		self.base_collection_finish_evt = base_collection_finish_evt
		self.session = None

		self.agent_in_q = None
		self.agent_out_q = None
		self.agents = []

		self.agent_cnt = agent_cnt
		if agent_cnt is None:
			self.agent_cnt = min(get_cpu_count(), 4)
		
		self.graph_id = graph_id
		self.resumption = False
		self.ad_id = ad_id

		if ad_id is not None:
			self.resumption = True
		self.domain_name = None

		self.members_target_file_name = None
		self.sd_target_file_name = None

		self.sd_task = None
		self.members_task = None
		self.stream_data = stream_data

	async def collect_members(self):
		try:
			self.members_file_handle = gzip.GzipFile(self.members_target_file_name,mode='rb')

			mc = MembershipCollector(
				self.session,
				self.ldap_mgr,
				ad_id = self.ad_id,
				agent_cnt = self.agent_cnt,
				resumption = False,
				progress_queue = self.progress_queue,
				show_progress = self.show_progress,
				graph_id = self.graph_id,
				members_target_file_handle = self.members_file_handle,
				store_to_db = self.store_to_db
			)
			_, err = await mc.run()
			if err is not None:
				raise err
			
			return True, None
		except Exception as e:
			return False, e
		
		finally:
			if self.members_target_file_name is not None:
				if self.members_file_handle is not None:
					try:
						self.members_file_handle.close()
					except:
						pass
				if self.store_to_db is True:
					try:
						os.unlink(self.members_target_file_name)
					except:
						pass

		

	async def collect_sd(self):
		try:
			self.sd_file_handle = gzip.GzipFile(self.sd_target_file_name,mode='rb')

			sdc = SDCollector(
				self.session, 
				self.ldap_mgr, 
				ad_id = self.ad_id, 
				graph_id = self.graph_id, 
				agent_cnt = self.agent_cnt, 
				sd_target_file_handle = self.sd_file_handle, 
				resumption = False, #self.resumption, 
				progress_queue = self.progress_queue, 
				show_progress = self.show_progress,
				store_to_db = self.store_to_db
			)
			
			_, err = await sdc.run()
			if err is not None:
				raise err
			return True, None
		except Exception as e:
			return False, e

		finally:
			if self.sd_target_file_name is not None:
				if self.sd_file_handle is not None:
					try:
						self.sd_file_handle.close()
					except:
						pass
				if self.store_to_db is True:
					try:
						os.unlink(self.sd_target_file_name)
					except:
						pass

	async def run(self):
		try:
			logger.debug('[+] Starting LDAP information acqusition. This might take a while...')
			self.session = get_session(self.db_conn)

			if self.no_work_dir is False:
				if self.work_dir is None:
					self.work_dir = pathlib.Path('./workdir')
					self.work_dir.mkdir(parents=True, exist_ok=True)
				if isinstance(self.work_dir, str) is True:
					self.work_dir = pathlib.Path(self.work_dir)
				
				self.members_target_file_name = str(self.work_dir.joinpath('temp_members_list.gz'))
				self.sd_target_file_name = str(self.work_dir.joinpath('temp_sd_list.gz'))
			
			else:
				self.members_target_file_name = 'temp_members_list.gz'
				self.sd_target_file_name = 'temp_sd_list.gz'

			if self.resumption is False:
				self.members_file_handle = gzip.GzipFile(self.members_target_file_name,mode='wb')
				self.sd_file_handle = gzip.GzipFile(self.sd_target_file_name,mode='wb')
				bc = BaseCollector(
					self.session, 
					self.ldap_mgr, 
					agent_cnt = self.agent_cnt, 
					progress_queue = self.progress_queue, 
					show_progress = self.show_progress,
					members_file_handle = self.members_file_handle,
					sd_file_handle = self.sd_file_handle,
					stream_data = self.stream_data
				)
				self.ad_id, self.graph_id, err = await bc.run()
				if err is False:
					return None, None, err

				if self.base_collection_finish_evt is not None:
					self.base_collection_finish_evt.set()
				self.members_file_handle.close()
				self.sd_file_handle.close()

				_, err = await self.collect_sd()
				if err is not None:
					raise err
				
				_, err = await self.collect_members()
				if err is not None:
					raise err
			
			else:
				adinfo = self.session.query(ADInfo).get(self.ad_id)
				self.graph_id = adinfo.graph_id
				if adinfo.ldap_sds_finished is True and adinfo.ldap_members_finished is True:
					return self.ad_id, self.graph_id, None

				if adinfo.ldap_sds_finished is False:
					self.session.query(JackDawSD).filter_by(ad_id = self.ad_id).delete()
					self.session.commit()

				if adinfo.ldap_members_finished is False:
					self.session.query(Edge).delete()
					self.session.commit()

				if adinfo.ldap_members_finished is False:
					self.members_file_handle = gzip.GzipFile(self.members_target_file_name,mode='wb')
				if adinfo.ldap_sds_finished is False:
					self.sd_file_handle = gzip.GzipFile(self.sd_target_file_name,mode='wb')

				res = self.session.query(ADInfo).get(self.ad_id)
				data = {
					'dn' : res.distinguishedName,
					'sid' : res.objectSid,
					'guid' : res.objectGUID,
					'object_type' : 'domain'
				}
				if adinfo.ldap_sds_finished is False:
					self.sd_file_handle.write(json.dumps(data).encode() + b'\r\n')

				q = self.session.query(ADUser).filter_by(ad_id = self.ad_id)
				for res in windowed_query(q, ADUser.id, 100):
					data = {
						'dn' : res.dn,
						'sid' : res.objectSid,
						'guid' : res.objectGUID,
						'object_type' : 'user'
					}
					if adinfo.ldap_sds_finished is False:
						self.sd_file_handle.write(json.dumps(data).encode() + b'\r\n')
					if adinfo.ldap_members_finished is False:
						self.members_file_handle.write(json.dumps(data).encode() + b'\r\n')

				q = self.session.query(Machine).filter_by(ad_id = self.ad_id)
				for res in windowed_query(q, Machine.id, 100):
					data = {
						'dn' : res.dn,
						'sid' : res.objectSid,
						'guid' : res.objectGUID,
						'object_type' : 'machine'
					}
					if adinfo.ldap_sds_finished is False:
						self.sd_file_handle.write(json.dumps(data).encode() + b'\r\n')
					if adinfo.ldap_members_finished is False:
						self.members_file_handle.write(json.dumps(data).encode() + b'\r\n')

				q = self.session.query(Group).filter_by(ad_id = self.ad_id)
				for res in windowed_query(q, Group.id, 100):
					data = {
						'dn' : res.dn,
						'sid' : res.objectSid,
						'guid' : res.objectGUID,
						'object_type' : 'group'
					}
					if adinfo.ldap_sds_finished is False:
						self.sd_file_handle.write(json.dumps(data).encode() + b'\r\n')
					if adinfo.ldap_members_finished is False:
						self.members_file_handle.write(json.dumps(data).encode() + b'\r\n')

				q = self.session.query(ADOU).filter_by(ad_id = self.ad_id)
				for res in windowed_query(q, ADOU.id, 100):
					data = {
						'dn' : res.dn,
						'sid' : None,
						'guid' : res.objectGUID,
						'object_type' : 'ou'
					}
					if adinfo.ldap_sds_finished is False:
						self.sd_file_handle.write(json.dumps(data).encode() + b'\r\n')

				q = self.session.query(GPO).filter_by(ad_id = self.ad_id)
				for res in windowed_query(q, GPO.id, 100):
					data = {
						'dn' : res.dn,
						'sid' : None,
						'guid' : res.objectGUID,
						'object_type' : 'gpo'
					}
					if adinfo.ldap_sds_finished is False:
						self.sd_file_handle.write(json.dumps(data).encode() + b'\r\n')

				if adinfo.ldap_members_finished is False:
					self.members_file_handle.close()
				if adinfo.ldap_sds_finished is False:
					self.sd_file_handle.close()
				

			logger.debug('[+] LDAP information acqusition finished!')
			return self.ad_id, self.graph_id, None
		except Exception as e:
			return None, None, e

		
			

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