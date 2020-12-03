
import re
import os
import asyncio
import datetime
import json

from jackdaw.dbmodel.graphinfo import GraphInfo, GraphInfoAD
from jackdaw.dbmodel.spnservice import SPNService
from jackdaw.dbmodel.adgroup import Group
from jackdaw.dbmodel.adinfo import ADInfo
from jackdaw.dbmodel.aduser import ADUser
from jackdaw.dbmodel.adcomp import Machine
from jackdaw.dbmodel.adou import ADOU
from jackdaw.dbmodel.adinfo import ADInfo
from jackdaw.dbmodel.adgpo import GPO
from jackdaw.dbmodel.adgplink import Gplink
from jackdaw.dbmodel.adtrust import ADTrust
from jackdaw.dbmodel.adspn import JackDawSPN
from jackdaw.dbmodel import get_session
from jackdaw.dbmodel.edge import Edge
from jackdaw.dbmodel.edgelookup import EdgeLookup


from jackdaw import logger
from jackdaw.common.cpucount import get_cpu_count
from jackdaw.gatherer.progress import *
from jackdaw.gatherer.ldap.agent.common import *
from jackdaw.gatherer.ldap.agent.agent import LDAPGathererAgent

from tqdm import tqdm

class BaseCollector:
	def __init__(self, session, ldap_mgr, agent_cnt = None, progress_queue = None, show_progress = True, members_file_handle = None, sd_file_handle = None, stream_data = False):
		self.session = session
		self.members_file_handle = members_file_handle
		self.sd_file_handle = sd_file_handle
		
		self.agent_cnt = agent_cnt
		if self.agent_cnt is None:
			self.agent_cnt = min(get_cpu_count(), 4)
		
		self.progress_queue = progress_queue
		self.show_progress = show_progress
	
		self.ldap_mgr = ldap_mgr
		self.agents = []

		self.agent_in_q = None
		self.agent_out_q = None
		self.ad_id = None
		self.domain_name = None

		self.total_progress = None
		self.total_counter = 0
		self.total_counter_steps = 100
		self.progress_last_updated = datetime.datetime.utcnow()
		self.progress_last_counter = 0
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
		self.schema_ctr = 0

		self.running_enums = {}
		self.finished_enums = []
		self.stream_data = stream_data

		self.enum_types = [
			'adinfo',
			'trusts',
			'users', 
			'machines',
			'groups',
			'ous', 
			'gpos',
			'spns',
			'schema',
		]
		self.enum_types_len = len(self.enum_types)

	@staticmethod
	def spn_to_account(spn):
		if spn.find('/') != -1:
			return spn.rsplit('/')[1].upper() + '$'


	async def update_progress(self):
		self.total_counter += 1

		if self.progress_queue is None:			
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
				msg = GathererProgress()
				msg.type = GathererProgressType.BASIC
				msg.msg_type = MSGTYPE.PROGRESS
				msg.adid = self.ad_id
				msg.domain_name = self.domain_name
				msg.finished = self.finished_enums
				msg.running = self.running_enums
				msg.total_finished = self.total_counter
				msg.step_size = self.total_counter_steps
				msg.speed = 0
				if td > 0:
					msg.speed = str(cd / td)

				await self.progress_queue.put(msg)
	
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

	async def stop_agents(self):
		logger.debug('mgr stop')

		info = self.session.query(ADInfo).get(self.ad_id)
		info.ldap_enumeration_state = 'FINISHED'
		self.session.commit()
		
		for _ in range(self.agent_cnt):
			await self.agent_in_q.put(None)

		try:
			await asyncio.wait_for(asyncio.gather(*self.agents), 10)
		except asyncio.TimeoutError:
			for agent in self.agents:
				agent.cancel()

		self.session.close()
		if self.total_progress is not None:
			self.total_progress.disable = True

		if self.progress_queue is not None:
			msg = GathererProgress()
			msg.type = GathererProgressType.BASIC
			msg.msg_type = MSGTYPE.FINISHED
			msg.adid = self.ad_id
			msg.domain_name = self.domain_name
			await self.progress_queue.put(msg)

		logger.debug('All agents finished!')


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
		
		graph = GraphInfo()
		self.session.add(graph)
		self.session.commit()
		self.session.refresh(graph)

		self.graph_id = graph.id
		giad = GraphInfoAD(self.ad_id, self.graph_id)
		self.session.add(giad)
		

		t = EdgeLookup(self.ad_id, info.objectSid, 'domain')
		self.session.add(t)

		data = {
				'dn' : info.distinguishedName,
				'sid' : info.objectSid,
				'guid' : info.objectGUID,
				'object_type' : 'domain'
		}
		if self.sd_file_handle is not None:
			self.sd_file_handle.write(json.dumps(data).encode() + b'\r\n')
		

	async def enum_trusts(self):
		logger.debug('Enumerating trusts')
		job = LDAPAgentJob(LDAPAgentCommand.TRUSTS, None)
		await self.agent_in_q.put(job)

	async def store_trust(self, trust):
		trust.ad_id = self.ad_id
		self.session.add(trust)
		t = EdgeLookup(self.ad_id, trust.securityIdentifier, 'trust')
		self.session.add(t)
		#self.session.flush()

	async def enum_users(self):
		logger.debug('Enumerating users')
		job = LDAPAgentJob(LDAPAgentCommand.USERS, self.ad_id)
		await self.agent_in_q.put(job)
		

	async def store_user(self, user_and_spn):
		user = user_and_spn['user']
		spns = user_and_spn['spns']
		user.ad_id = self.ad_id
		self.session.add(user)
		t = EdgeLookup(self.ad_id, user.objectSid, 'user')
		self.session.add(t)
		for spn in spns:
			spn.ad_id = self.ad_id
			self.session.add(spn)

		if self.stream_data is True and self.progress_queue is not None:
			msg = GathererProgress()
			msg.type = GathererProgressType.USER
			msg.msg_type = MSGTYPE.FINISHED
			msg.adid = self.ad_id
			msg.domain_name = self.domain_name
			msg.data = user
			await self.progress_queue.put(msg)


		#self.session.flush()

		data = {
				'dn' : user.dn,
				'sid' : user.objectSid,
				'guid' : user.objectGUID,
				'object_type' : 'user'
		}
		if self.sd_file_handle is not None:
			self.sd_file_handle.write(json.dumps(data).encode() + b'\r\n')
		if self.members_file_handle is not None:
			self.members_file_handle.write(json.dumps(data).encode() + b'\r\n')
		

	async def enum_machines(self):
		logger.debug('Enumerating machines')
		job = LDAPAgentJob(LDAPAgentCommand.MACHINES, self.ad_id)
		await self.agent_in_q.put(job)

	async def store_machine(self, machine_and_del):
		machine = machine_and_del['machine']
		delegations = machine_and_del['delegations']
		allowedtoact = machine_and_del['allowedtoact']
		machine.ad_id = self.ad_id
		t = EdgeLookup(self.ad_id, machine.objectSid, 'machine')
		self.session.add(t)
		self.session.add(machine)
		#self.session.commit()
		#self.session.refresh(machine)
		for d in delegations:
			d.machine_sid = machine.objectSid
			d.ad_id = self.ad_id
			self.session.add(d)

		for aa in allowedtoact:
			aa.ad_id = self.ad_id
			self.session.add(aa)
		#self.session.commit()
		#self.session.flush()
		
		if self.stream_data is True and self.progress_queue is not None:
			msg = GathererProgress()
			msg.type = GathererProgressType.MACHINE
			msg.msg_type = MSGTYPE.FINISHED
			msg.adid = self.ad_id
			msg.domain_name = self.domain_name
			msg.data = machine
			await self.progress_queue.put(msg)

		data = {
				'dn' : machine.dn,
				'sid' : machine.objectSid,
				'guid' : machine.objectGUID,
				'object_type' : 'machine'
		}
		if self.sd_file_handle is not None:
			self.sd_file_handle.write(json.dumps(data).encode() + b'\r\n')
		if self.members_file_handle is not None:
			self.members_file_handle.write(json.dumps(data).encode() + b'\r\n')

	async def enum_schema(self):
		logger.debug('Enumerating groups')
		job = LDAPAgentJob(LDAPAgentCommand.SCHEMA, self.ad_id)
		await self.agent_in_q.put(job)

	
	async def store_schema(self, se):
		se.ad_id = self.ad_id
		self.session.add(se)
	
	async def enum_groups(self):
		logger.debug('Enumerating groups')
		job = LDAPAgentJob(LDAPAgentCommand.GROUPS, self.ad_id)
		await self.agent_in_q.put(job)

	async def store_group(self, group):
		group.ad_id = self.ad_id
		t = EdgeLookup(self.ad_id, group.objectSid, 'group')
		self.session.add(t)
		self.session.add(group)
		#self.session.flush()

		data = {
				'dn' : group.dn,
				'sid' : group.objectSid,
				'guid' : group.objectGUID,
				'object_type' : 'group'
		}
		if self.sd_file_handle is not None:
			self.sd_file_handle.write(json.dumps(data).encode() + b'\r\n')
		if self.members_file_handle is not None:
			self.members_file_handle.write(json.dumps(data).encode() + b'\r\n')
		
		if self.stream_data is True and self.progress_queue is not None:
			msg = GathererProgress()
			msg.type = GathererProgressType.GROUP
			msg.msg_type = MSGTYPE.FINISHED
			msg.adid = self.ad_id
			msg.domain_name = self.domain_name
			msg.data = group
			await self.progress_queue.put(msg)

	async def enum_ous(self):
		logger.debug('Enumerating ous')
		job = LDAPAgentJob(LDAPAgentCommand.OUS, self.ad_id)
		await self.agent_in_q.put(job)

	async def store_ous(self, ou):
		ou.ad_id = self.ad_id
		self.session.add(ou)
		#self.session.commit()
		#self.session.refresh(ou)
		t = EdgeLookup(self.ad_id, ou.objectGUID, 'ou')
		self.session.add(t)

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

				link = Gplink()
				link.ad_id = self.ad_id
				link.ou_guid = ou.objectGUID
				link.gpo_dn = gp
				link.order = order
				self.session.add(link)
		#self.session.flush()

		data = {
				'dn' : ou.dn,
				'sid' : None,
				'guid' : ou.objectGUID,
				'object_type' : 'ou'
		}
		if self.sd_file_handle is not None:
			self.sd_file_handle.write(json.dumps(data).encode() + b'\r\n')

	async def enum_spnservices(self):		
		logger.debug('Enumerating spns')
		job = LDAPAgentJob(LDAPAgentCommand.SPNSERVICES, self.ad_id)
		await self.agent_in_q.put(job)

	async def store_spn(self, spn):
		spn.ad_id = self.ad_id
		self.session.add(spn)
		#self.session.flush()

	async def enum_gpos(self):
		logger.debug('Enumerating gpos')
		job = LDAPAgentJob(LDAPAgentCommand.GPOS, self.ad_id)
		await self.agent_in_q.put(job)

	async def store_gpo(self, gpo):
		gpo.ad_id = self.ad_id
		self.session.add(gpo)
		#self.session.flush()
		t = EdgeLookup(self.ad_id, gpo.objectGUID, 'gpo')
		self.session.add(t)

		data = {
				'dn' : gpo.dn,
				'sid' : None,
				'guid' : gpo.objectGUID,
				'object_type' : 'gpo'
		}
		if self.sd_file_handle is not None:
			self.sd_file_handle.write(json.dumps(data).encode() + b'\r\n')


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
				elif next_type == 'schema':
					await self.enum_schema()
				else:
					logger.warning('Unknown next_type! %s' % next_type)

				self.running_enums[next_type] = 1

			return False

	async def run(self):
		logger.debug('Basecollector started!')

		qs = self.agent_cnt
		self.agent_in_q = asyncio.Queue() #AsyncProcessQueue()
		self.agent_out_q = asyncio.Queue(qs) #AsyncProcessQueue(1000)

		if self.show_progress is True:
			self.total_progress = tqdm(desc='LDAP info entries', ascii = True)
		
		
		for _ in range(self.agent_cnt):
			agent = LDAPGathererAgent(self.ldap_mgr, self.agent_in_q, self.agent_out_q)
			self.agents.append(asyncio.create_task(agent.arun()))

		if self.progress_queue is not None:
			msg = GathererProgress()
			msg.type = GathererProgressType.BASIC
			msg.msg_type = MSGTYPE.STARTED
			msg.adid = self.ad_id
			msg.domain_name = self.domain_name
			await self.progress_queue.put(msg)

		await self.check_jobs(None)

		logger.debug('basecollector setup complete!')
		try:
			while True:
				res = await self.agent_out_q.get()
				await self.update_progress()
				res_type, res = res

				if res_type == LDAPAgentCommand.DOMAININFO:
					self.domaininfo_ctr += 1
					await self.store_domain(res)
				
				elif res_type == LDAPAgentCommand.USER:
					self.user_ctr += 1
					await self.store_user(res)
					if self.user_ctr % 1000 == 0:
						self.session.commit()

				elif res_type == LDAPAgentCommand.MACHINE:
					self.machine_ctr += 1
					await self.store_machine(res)
					if self.machine_ctr % 1000 == 0:
						self.session.commit()

				elif res_type == LDAPAgentCommand.GROUP:
					self.group_ctr += 1
					await self.store_group(res)
					if self.group_ctr % 1000 == 0:
						self.session.commit()

				elif res_type == LDAPAgentCommand.OU:
					self.ou_ctr += 1
					await self.store_ous(res)

				elif res_type == LDAPAgentCommand.GPO:
					self.gpo_ctr += 1
					await self.store_gpo(res)

				elif res_type == LDAPAgentCommand.SPNSERVICE:
					self.spn_ctr += 1
					await self.store_spn(res)

				elif res_type == LDAPAgentCommand.TRUSTS:
					self.trust_ctr += 1
					await self.store_trust(res)

				elif res_type == LDAPAgentCommand.SCHEMA:
					self.schema_ctr += 1
					await self.store_schema(res)

				elif res_type == LDAPAgentCommand.EXCEPTION:
					logger.warning(str(res))
					
				elif res_type.name.endswith('FINISHED'):
					t = await self.check_jobs(res_type)
					self.session.commit()
					if t is True:
						break
		
			return self.ad_id, self.graph_id, None
		except Exception as e:
			logger.exception('ldap enumerator main!')
			return None, None, e

		finally:
			await self.stop_agents()
		
		
		