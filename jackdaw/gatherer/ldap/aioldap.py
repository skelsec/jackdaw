#!/usr/bin/env python3
#
# Author:
#  Tamas Jos (@skelsec)
#

import os
import re
import enum
import base64
import asyncio
import datetime
import threading
import traceback
import multiprocessing

from jackdaw.dbmodel.spnservice import JackDawSPNService
from jackdaw.dbmodel.addacl import JackDawADDACL
from jackdaw.dbmodel.adgroup import JackDawADGroup
from jackdaw.dbmodel.adinfo import JackDawADInfo
from jackdaw.dbmodel.aduser import JackDawADUser
from jackdaw.dbmodel.adcomp import JackDawADMachine
from jackdaw.dbmodel.adou import JackDawADOU
from jackdaw.dbmodel.usergroup import JackDawGroupUser
from jackdaw.dbmodel.adinfo import JackDawADInfo
from jackdaw.dbmodel.tokengroup import JackDawTokenGroup
from jackdaw.dbmodel.adgpo import JackDawADGPO
from jackdaw.dbmodel.constrained import JackDawMachineConstrainedDelegation, JackDawUserConstrainedDelegation
from jackdaw.dbmodel.adgplink import JackDawADGplink
from jackdaw.dbmodel.adsd import JackDawSD
from jackdaw.dbmodel.adtrust import JackDawADTrust
from jackdaw.dbmodel import get_session
from jackdaw.wintypes.lookup_tables import *
from jackdaw import logger

from jackdaw.common.apq import AsyncProcessQueue

from msldap.ldap_objects import *
from winacl.dtyp.security_descriptor import SECURITY_DESCRIPTOR
from tqdm import tqdm

class LDAPEnumeratorProgress:
	def __init__(self):
		self.type = 'LDAP'
		self.msg_type = 'PROGRESS'
		self.adid = None
		self.domain_name = None
		self.finished = None
		self.running = None
		self.total_finished = None
		self.speed = None #per sec

	def __str__(self):
		if self.msg_type == 'PROGRESS':
			return '[%s][%s][%s][%s] FINISHED %s RUNNING %s TOTAL %s SPEED %s' % (
				self.type, 
				self.domain_name, 
				self.adid,
				self.msg_type,
				','.join(self.finished), 
				','.join(self.running), 
				self.total_finished, 
				self.speed
			
			)
		return '[%s][%s][%s][%s]' % (self.type, self.domain_name, self.adid, self.msg_type)

class LDAPAgentCommand(enum.Enum):
	SPNSERVICE = 0
	SPNSERVICES = 1
	USER = 2
	USERS = 3
	MACHINE = 4
	MACHINES = 5
	OU = 6
	OUS = 7
	DOMAININFO = 8
	GROUP = 9
	GROUPS = 10
	MEMBERSHIP = 11
	MEMBERSHIPS = 12
	SD = 13
	SDS = 14
	GPO = 15
	GPOS = 16
	TRUSTS = 17
	EXCEPTION = 99

	SPNSERVICES_FINISHED = 31
	USERS_FINISHED = 32
	MACHINES_FINISHED = 33
	OUS_FINISHED = 34
	GROUPS_FINISHED = 35
	MEMBERSHIPS_FINISHED = 36
	SDS_FINISHED = 37
	DOMAININFO_FINISHED = 38
	GPOS_FINISHED = 39
	TRUSTS_FINISHED = 40

MSLDAP_JOB_TYPES = {
	'users' : LDAPAgentCommand.USERS_FINISHED ,
	'machines' : LDAPAgentCommand.MACHINES_FINISHED ,
	'sds' : LDAPAgentCommand.SDS_FINISHED ,
	'memberships' : LDAPAgentCommand.MEMBERSHIPS_FINISHED ,
	'ous' : LDAPAgentCommand.OUS_FINISHED ,
	'gpos' : LDAPAgentCommand.GPOS_FINISHED ,
	'groups' : LDAPAgentCommand.GROUPS_FINISHED ,
	'spns' : LDAPAgentCommand.SPNSERVICES_FINISHED ,
	'adinfo' : LDAPAgentCommand.DOMAININFO_FINISHED,
	'trusts' : LDAPAgentCommand.TRUSTS_FINISHED
}
MSLDAP_JOB_TYPES_INV = {v: k for k, v in MSLDAP_JOB_TYPES.items()}

class LDAPAgentJob:
	def __init__(self, command, data):
		self.command = command
		self.data = data

class LDAPEnumeratorAgent():
	def __init__(self, ldap_mgr, agent_in_q, agent_out_q):
		#multiprocessing.Process.__init__(self)
		self.ldap_mgr = ldap_mgr
		self.agent_in_q = agent_in_q
		self.agent_out_q = agent_out_q
		self.ldap = None
		self.test_ctr = 0

	async def get_all_effective_memberships(self):
		try:
			async for res, err in self.ldap.get_all_tokengroups():
				if err is not None:
					raise err
				s = JackDawTokenGroup()
				s.cn = res['cn']
				s.dn = res['dn']
				s.guid = res['guid']
				s.sid = res['sid']
				s.member_sid = res['token']
				s.is_user = True if res['type'] == 'user' else False
				s.is_group = True if res['type'] == 'group' else False
				s.is_machine = True if res['type'] == 'computer' else False
				await self.agent_out_q.put((LDAPAgentCommand.MEMBERSHIP, s))
		except:
			await self.agent_out_q.put((LDAPAgentCommand.EXCEPTION, str(traceback.format_exc())))
		finally:
			await self.agent_out_q.put((LDAPAgentCommand.MEMBERSHIPS_FINISHED, None))

	async def enumerate_spnservices(self):
		pass

	async def enumerate_machine(self, machine):
		pass

	async def get_all_trusts(self):
		try:
			async for entry, err in self.ldap.get_all_trusts():
				if err is not None:
					raise err
				await self.agent_out_q.put((LDAPAgentCommand.TRUSTS, JackDawADTrust.from_ldapdict(entry.to_dict())))
		except:
			await self.agent_out_q.put((LDAPAgentCommand.EXCEPTION, str(traceback.format_exc())))
		finally:
			await self.agent_out_q.put((LDAPAgentCommand.TRUSTS_FINISHED, None))

	async def get_all_spnservices(self):
		try:
			async for entry, err in self.ldap.get_all_spn_entries():
				if err is not None:
					raise err
				for spn in entry['attributes']['servicePrincipalName']:
					port = None
					service, t = spn.rsplit('/',1)
					m = t.find(':')
					if m != -1:
						computername, port = spn.rsplit(':',1)
					else:
						computername = t

					s = JackDawSPNService()
					s.owner_sid = str(entry['attributes']['objectSid'])
					s.computername = computername
					s.service = service
					s.port = port
					await self.agent_out_q.put((LDAPAgentCommand.SPNSERVICE, s))
		except:
			await self.agent_out_q.put((LDAPAgentCommand.EXCEPTION, str(traceback.format_exc())))
		finally:
			await self.agent_out_q.put((LDAPAgentCommand.SPNSERVICES_FINISHED, None))

	async def get_all_users(self):
		try:
			async for user_data, err in self.ldap.get_all_users():
				if err is not None:
					raise err
				user = JackDawADUser.from_aduser(user_data)
				await self.agent_out_q.put((LDAPAgentCommand.USER, user))
		except:
			await self.agent_out_q.put((LDAPAgentCommand.EXCEPTION, str(traceback.format_exc())))
		finally:
			await self.agent_out_q.put((LDAPAgentCommand.USERS_FINISHED, None))

	async def get_all_groups(self):
		try:
			async for group, err in self.ldap.get_all_groups():
				if err is not None:
					raise err
				g = JackDawADGroup.from_dict(group.to_dict())
				await self.agent_out_q.put((LDAPAgentCommand.GROUP, g))
				del g
		except:
			await self.agent_out_q.put((LDAPAgentCommand.EXCEPTION, str(traceback.format_exc())))
		finally:
			await self.agent_out_q.put((LDAPAgentCommand.GROUPS_FINISHED, None))

	async def get_all_gpos(self):
		try:
			async for gpo, err in self.ldap.get_all_gpos():
				if err is not None:
					raise err
				g = JackDawADGPO.from_adgpo(gpo)
				await self.agent_out_q.put((LDAPAgentCommand.GPO, g))
				del g
		except:
			await self.agent_out_q.put((LDAPAgentCommand.EXCEPTION, str(traceback.format_exc())))
		finally:
			await self.agent_out_q.put((LDAPAgentCommand.GPOS_FINISHED, None))


	async def get_all_machines(self):
		try:
			async for machine_data, err in self.ldap.get_all_machines():
				if err is not None:
					raise err
				machine = JackDawADMachine.from_adcomp(machine_data)
				await self.agent_out_q.put((LDAPAgentCommand.MACHINE, machine))
		except:
			await self.agent_out_q.put((LDAPAgentCommand.EXCEPTION, str(traceback.format_exc())))
		finally:
			await self.agent_out_q.put((LDAPAgentCommand.MACHINES_FINISHED, None))

	async def get_all_ous(self):
		try:
			async for ou, err in self.ldap.get_all_ous():
				if err is not None:
					raise err
				o = JackDawADOU.from_adou(ou)
				await self.agent_out_q.put((LDAPAgentCommand.OU, o))
				del o
		except:
			await self.agent_out_q.put((LDAPAgentCommand.EXCEPTION, str(traceback.format_exc())))
		finally:
			await self.agent_out_q.put((LDAPAgentCommand.OUS_FINISHED, None))

	async def get_domain_info(self):
		try:
			info, err = await self.ldap.get_ad_info()
			if err is not None:
				raise err
			adinfo = JackDawADInfo.from_dict(info.to_dict())
			await self.agent_out_q.put((LDAPAgentCommand.DOMAININFO, adinfo))
		except:
			await self.agent_out_q.put((LDAPAgentCommand.EXCEPTION, str(traceback.format_exc())))
		finally:
			await self.agent_out_q.put((LDAPAgentCommand.DOMAININFO_FINISHED, None))

	async def get_sds(self, data):
		try:
			async for adsec, err in self.ldap.get_all_objectacl():
				if err is not None:
					raise err
				if not adsec.nTSecurityDescriptor:
					continue
				await self.agent_out_q.put((LDAPAgentCommand.SD, adsec ))

		except:
			await self.agent_out_q.put((LDAPAgentCommand.EXCEPTION, str(traceback.format_exc())))
		finally:
			await self.agent_out_q.put((LDAPAgentCommand.SDS_FINISHED, None))

	async def setup(self):
		try:
			self.ldap = self.ldap_mgr.get_client()
			res, err = await self.ldap.connect()
			if err is not None:
				raise err
			return res
		except:
			await self.agent_out_q.put((LDAPAgentCommand.EXCEPTION, str(traceback.format_exc())))
			return False

	async def arun(self):
		res = await self.setup()
		if res is False:
			return
		while True:
			res = await self.agent_in_q.get()
			if res is None:
				return

			if res.command == LDAPAgentCommand.DOMAININFO:
				await self.get_domain_info()
			elif res.command == LDAPAgentCommand.USERS:
				await self.get_all_users()
			elif res.command == LDAPAgentCommand.MACHINES:
				await self.get_all_machines()
			elif res.command == LDAPAgentCommand.GROUPS:
				await self.get_all_groups()
			elif res.command == LDAPAgentCommand.OUS:
				await self.get_all_ous()
			elif res.command == LDAPAgentCommand.GPOS:
				await self.get_all_gpos()
			elif res.command == LDAPAgentCommand.SPNSERVICES:
				await self.get_all_spnservices()
			elif res.command == LDAPAgentCommand.MEMBERSHIPS:
				await self.get_all_effective_memberships()
			elif res.command == LDAPAgentCommand.SDS:
				await self.get_sds(res.data)
			elif res.command == LDAPAgentCommand.TRUSTS:
				await self.get_all_trusts()

	def run(self):
		try:
			loop = asyncio.get_event_loop()
		except:
			loop = asyncio.new_event_loop()
		#loop.set_debug(True)  # Enable debug
		loop.run_until_complete(self.arun())

class LDAPEnumeratorManager:
	def __init__(self, db_conn, ldam_mgr, agent_cnt = None, queue_size = None, progress_queue = None):
		self.db_conn = db_conn
		self.ldam_mgr = ldam_mgr

		self.session = None

		self.queue_size = queue_size
		self.agent_in_q = None
		self.agent_out_q = None
		self.agents = []

		self.agent_cnt = agent_cnt
		if agent_cnt is None:
			self.agent_cnt = min(multiprocessing.cpu_count(), 3)

		self.ad_id = None
		self.domain_name = None

		self.user_ctr = 0
		self.machine_ctr = 0
		self.ou_ctr = 0
		self.group_ctr = 0
		self.sd_ctr = 0
		self.spn_ctr = 0
		self.member_ctr = 0
		self.domaininfo_ctr = 0
		self.gpo_ctr = 0
		self.trust_ctr = 0

		self.user_finish_ctr = 0
		self.machine_finish_ctr = 0
		self.ou_finish_ctr = 0
		self.group_finish_ctr = 0
		self.sd_finish_ctr = 0
		self.spn_finish_ctr = 0
		self.member_finish_ctr = 0
		self.domaininfo_finish_ctr = 0
		self.gpo_finish_ctr = 0

		self.progress_queue = progress_queue
		self.total_progress = None
		self.total_counter = 0
		self.total_counter_steps = 100
		self.progress_total_present = False
		self.remaining_ctr = None
		self.progress_last_updated = datetime.datetime.utcnow()
		self.progress_last_counter = 0

		self.enum_finished_evt = None #multiprocessing.Event()
		
		self.running_enums = {}
		self.finished_enums = []
		self.enum_types = [
			'adinfo',
			'trusts',
			'users', 
			'machines',
			'groups',
			'memberships', 
			'sds', 
			'ous', 
			'gpos',
			'spns'
		]
		self.enum_types_len = len(self.enum_types)

	async def check_jobs(self, finished_type):
		self.session.commit()
		if finished_type is not None:
			logger.debug('%s enumeration finished!' % MSLDAP_JOB_TYPES_INV[finished_type])
			del self.running_enums[MSLDAP_JOB_TYPES_INV[finished_type]]
			self.finished_enums.append(MSLDAP_JOB_TYPES_INV[finished_type])

		lr = len(self.running_enums)
		if self.enum_types_len == len(self.finished_enums):
			#everything finished
			return True

		if lr == self.agent_cnt:
			#enums still running with max performance
			return False

		if lr < self.agent_cnt:
			#we can start a new enum
			for _ in range(self.agent_cnt - lr):
				if len(self.enum_types) > 0:
					next_type = self.enum_types.pop(0)
				else:
					return False
				
				if next_type == 'adinfo':
					await self.enum_domain()
					#this must be the first!
					self.running_enums[next_type] = 1
					return False
				
				elif next_type == 'users':
					await self.enum_users()

				elif next_type == 'machines':
					await self.enum_machines()
				elif next_type == 'sds':
					await self.enum_sds()
				elif next_type == 'memberships':
					await self.enum_memberships()
				elif next_type == 'ous':
					await self.enum_ous()
				elif next_type == 'gpos':
					await self.enum_gpos()
				elif next_type == 'groups':
					await self.enum_groups()
				elif next_type == 'spns':
					await self.enum_spnservices()
				elif next_type == 'trusts':
					await self.enum_trusts()
				else:
					logger.warning('Unknown next_type! %s' % next_type)

				self.running_enums[next_type] = 1

			return False
		

	@staticmethod
	def spn_to_account(spn):
		if spn.find('/') != -1:
			return spn.rsplit('/')[1].upper() + '$'
	
	def get_enum_stats(self):
		return {
			'users' : self.user_ctr,
			'machines' : self.machine_ctr,
			'ous' : self.ou_ctr,
			'groups' : self.group_ctr,
			'security_descriptors' : self.sd_ctr,
			'spns' : self.spn_ctr,
			'membership_tokens' : self.member_ctr,
			'domaininfo' : self.domaininfo_ctr,
			'gpos' : self.gpo_ctr,
		}

	async def setup(self):
		logger.debug('mgr setup')

		qs = self.queue_size
		if qs is None:
			qs = self.agent_cnt
		self.agent_in_q = asyncio.Queue() #AsyncProcessQueue()
		self.agent_out_q = asyncio.Queue(qs) #AsyncProcessQueue(1000)

		if self.progress_queue is None:
			self.total_progress = tqdm(desc='LDAP info entries', ascii = True)
		
		self.session = get_session(self.db_conn)
		
		for _ in range(self.agent_cnt):
			agent = LDAPEnumeratorAgent(self.ldam_mgr, self.agent_in_q, self.agent_out_q)
			self.agents.append(asyncio.create_task(agent.arun()))
			#agent.daemon = True
			#agent.start()
			#self.agents.append(agent)

	async def terminate(self):
		logger.debug('terminate called!')
		if self.progress_queue is None:
			msg = LDAPEnumeratorProgress()
			msg.type = 'LDAP'
			msg.msg_type = 'ABORTED'
			msg.adid = self.ad_id
			msg.domain_name = self.domain_name
			await self.progress_queue.put(msg)

		for task in self.agents:
			task.cancel()
		try:
			self.session.commit()
		except:
			pass
		
		try:
			self.session.close()
		except:
			pass

	async def enum_domain(self):
		logger.debug('Enumerating domain')
		job = LDAPAgentJob(LDAPAgentCommand.DOMAININFO, None)
		await self.agent_in_q.put(job)

	async def store_domain(self, info):
		info.ldap_enumeration_state = 'STARTED'
		self.domain_name = str(info.distinguishedName).replace(',','.').replace('DC=','')
		self.session.add(info)
		self.session.commit()
		self.session.refresh(info)
		self.ad_id = info.id

	async def enum_trusts(self):
		logger.debug('Enumerating trusts')
		job = LDAPAgentJob(LDAPAgentCommand.TRUSTS, None)
		await self.agent_in_q.put(job)

	async def store_trust(self, trust):
		trust.ad_id = self.ad_id
		self.session.add(trust)
		self.session.flush()

	async def enum_users(self):
		logger.debug('Enumerating users')
		job = LDAPAgentJob(LDAPAgentCommand.USERS, self.ad_id)
		await self.agent_in_q.put(job)
		

	async def store_user(self, user):
		user.ad_id = self.ad_id

		#self.session.flush()
		#self.session.refresh(user)

		for spn in getattr(user,'allowedtodelegateto',[]):
			con = JackDawUserConstrainedDelegation()
			con.spn = spn
			con.targetaccount = LDAPEnumeratorManager.spn_to_account(spn)
			user.allowedtodelegateto.append(con)

		self.session.add(user)
		self.session.flush()

	async def enum_machines(self):
		logger.debug('Enumerating machines')
		job = LDAPAgentJob(LDAPAgentCommand.MACHINES, self.ad_id)
		await self.agent_in_q.put(job)

	async def store_machine(self, machine):
		machine.ad_id = self.ad_id
		self.session.add(machine)
		#self.session.commit()
		self.session.flush()
	
	async def enum_groups(self):
		logger.debug('Enumerating groups')
		job = LDAPAgentJob(LDAPAgentCommand.GROUPS, self.ad_id)
		await self.agent_in_q.put(job)

	async def store_group(self, group):
		group.ad_id = self.ad_id
		self.session.add(group)
		self.session.flush()

	async def enum_ous(self):
		logger.debug('Enumerating ous')
		job = LDAPAgentJob(LDAPAgentCommand.OUS, self.ad_id)
		await self.agent_in_q.put(job)

	async def store_ous(self, ou):
		ou.ad_id = self.ad_id
		self.session.add(ou)
		self.session.commit()
		self.session.refresh(ou)

		if ou.gPLink is not None and ou.gPLink != 'None':
			for x in ou.gPLink.split(']'):
				if x is None or x == 'None':
					continue
				x = x.strip()
				if x == '':
					continue
				gp, order = x[1:].split(';')
				gp = re.search(r'{(.*?)}', gp).group(1)
				gp = '{' + gp + '}'

				link = JackDawADGplink()
				link.ent_id = ou.id
				link.gpo_dn = gp
				link.order = order
				self.session.add(link)
		self.session.flush()

	async def enum_spnservices(self):		
		logger.debug('Enumerating spns')
		job = LDAPAgentJob(LDAPAgentCommand.SPNSERVICES, self.ad_id)
		await self.agent_in_q.put(job)

	async def store_spn(self, spn):
		spn.ad_id = self.ad_id
		self.session.add(spn)
		self.session.flush()

	async def enum_gpos(self):
		logger.debug('Enumerating gpos')
		job = LDAPAgentJob(LDAPAgentCommand.GPOS, self.ad_id)
		await self.agent_in_q.put(job)

	async def store_gpo(self, gpo):
		gpo.ad_id = self.ad_id
		self.session.add(gpo)
		self.session.flush()

	async def enum_memberships(self):
		logger.debug('Enumerating memberships')
		job = LDAPAgentJob(LDAPAgentCommand.MEMBERSHIPS, None)
		await self.agent_in_q.put(job)


	async def store_membership(self, res):
		res.ad_id = self.ad_id
		self.session.add(res)
		
		if self.member_finish_ctr % 1000 == 0:
			self.session.commit()
		else:
			self.session.flush()

	async def enum_sds(self):
		logger.debug('Enumerating security descriptors')
		job = LDAPAgentJob(LDAPAgentCommand.SDS, None)
		await self.agent_in_q.put(job)

	async def store_sd(self, sd):
		#secdesc = SECURITY_DESCRIPTOR.from_bytes(sd.nTSecurityDescriptor)
		#
		if sd.objectClass[-1] in ['user', 'group']:
			obj_type = sd.objectClass[-1]
		elif sd.objectClass[-1] == 'computer':
			obj_type = 'machine'
		elif sd.objectClass[-1] == 'groupPolicyContainer':
			obj_type = 'gpo'
		elif sd.objectClass[-1] == 'organizationalUnit':
			obj_type = 'ou'
		else:
			obj_type = sd.objectClass[-1]

		jdsd = JackDawSD()

		jdsd.ad_id = self.ad_id
		jdsd.guid =  str(sd.objectGUID)
		if sd.objectSid:
			jdsd.sid = str(sd.objectSid)
		jdsd.object_type = obj_type
		jdsd.sd = base64.b64encode(sd.nTSecurityDescriptor)
		
		self.session.add(jdsd)
		
		if self.sd_ctr % 1000 == 0:
			self.session.commit()
		else:
			self.session.flush()

	async def update_progress(self):
		self.total_counter += 1

		if self.progress_queue is None:
			#if self.remaining_ctr is not None and self.progress_total_present is False:
			#	self.total_progress.total = (self.remaining_ctr +  self.total_counter)
			#	self.progress_total_present = True
			
			if self.total_counter % self.total_counter_steps == 0:
				self.total_progress.update(self.total_counter_steps)

			if self.total_counter % 5000 == 0:
				running_jobs = ','.join([k for k in self.running_enums])
				finished_jobs = ','.join(self.finished_enums)
				msg = 'FINISHED: %s RUNNING: %s' % (finished_jobs, running_jobs)
				#logger.debug(msg)
				self.total_progress.set_description(msg)
				self.total_progress.refresh()
		
		else:
			if self.total_counter % self.total_counter_steps == 0:
				now = datetime.datetime.utcnow()
				td = (now - self.progress_last_updated).total_seconds()
				self.progress_last_updated = now
				cd = self.total_counter - self.progress_last_counter
				self.progress_last_counter = self.total_counter
				msg = LDAPEnumeratorProgress()
				msg.type = 'LDAP'
				msg.msg_type = 'PROGRESS'
				msg.adid = self.ad_id
				msg.domain_name = self.domain_name
				msg.finished = self.finished_enums
				msg.running = self.running_enums
				msg.total_finished = self.total_counter
				msg.speed = str(cd / td)

				await self.progress_queue.put(msg)

	async def stop_agents(self):
		logger.debug('mgr stop')

		info = self.session.query(JackDawADInfo).get(self.ad_id)
		info.ldap_enumeration_state = 'FINISHED'
		self.session.commit()
		self.session.close()
		for _ in range(self.agent_cnt):
			await self.agent_in_q.put(None)

		await asyncio.sleep(1)
		for agent in self.agents:
			agent.cancel()

		if self.progress_queue is not None:
			msg = LDAPEnumeratorProgress()
			msg.type = 'LDAP'
			msg.msg_type = 'FINISHED'
			msg.adid = self.ad_id
			msg.domain_name = self.domain_name
			await self.progress_queue.put(msg)

		logger.debug('All agents finished!')

	async def run(self):
		logger.info('[+] Starting LDAP information acqusition. This might take a while...')
		
		await self.setup()
		

		if self.progress_queue is not None:
			msg = LDAPEnumeratorProgress()
			msg.type = 'LDAP'
			msg.msg_type = 'STARTED'
			msg.adid = self.ad_id
			msg.domain_name = self.domain_name
			await self.progress_queue.put(msg)

		await self.check_jobs(None)

		while True:
			try:
				res = await self.agent_out_q.get()
				await self.update_progress()
				res_type, res = res

				if res_type == LDAPAgentCommand.DOMAININFO:
					self.domaininfo_ctr += 1
					await self.store_domain(res)
				
				elif res_type == LDAPAgentCommand.USER:
					self.user_ctr += 1
					await self.store_user(res)

				elif res_type == LDAPAgentCommand.MACHINE:
					self.machine_ctr += 1
					await self.store_machine(res)

				elif res_type == LDAPAgentCommand.GROUP:
					self.group_ctr += 1
					await self.store_group(res)

				elif res_type == LDAPAgentCommand.OU:
					self.ou_ctr += 1
					await self.store_ous(res)

				elif res_type == LDAPAgentCommand.GPO:
					self.gpo_ctr += 1
					await self.store_gpo(res)

				elif res_type == LDAPAgentCommand.SPNSERVICE:
					self.spn_ctr += 1
					await self.store_spn(res)
					
				elif res_type == LDAPAgentCommand.SD:
					self.sd_ctr += 1
					await self.store_sd(res)
					
				elif res_type == LDAPAgentCommand.MEMBERSHIP:
					self.member_ctr += 1
					await self.store_membership(res)

				elif res_type == LDAPAgentCommand.TRUSTS:
					self.trust_ctr += 1
					await self.store_trust(res)

				elif res_type == LDAPAgentCommand.EXCEPTION:
					logger.warning(str(res))
					
				elif res_type.name.endswith('FINISHED'):
					t = await self.check_jobs(res_type)
					if t is True:
						break
			except Exception as e:
				logger.exception('ldap enumerator main!')
				await self.stop_agents()
				return None
			
		await self.stop_agents()
		logger.info('[+] LDAP information acqusition finished!')
		return self.ad_id
			

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