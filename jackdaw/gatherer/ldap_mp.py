import traceback
import os
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
from jackdaw.dbmodel import *
from jackdaw.wintypes.lookup_tables import *
from jackdaw import logger

from msldap.ldap_objects import *

import multiprocessing
import enum

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
	EXCEPTION = 99

	SPNSERVICES_FINISHED = 31
	USERS_FINISHED = 32
	MACHINES_FINISHED = 33
	OUS_FINISHED = 34
	GROUPS_FINISHED = 35
	MEMBERSHIPS_FINISHED = 36
	SDS_FINISHED = 37
	DOMAININFO_FINISHED = 38

class LDAPAgentJob:
	def __init__(self, command, data):
		self.command = command
		self.data = data

class LDAPEnumeratorAgent(multiprocessing.Process):
	def __init__(self, ldap_mgr, agent_in_q, agent_out_q):
		multiprocessing.Process.__init__(self)
		self.ldap_mgr = ldap_mgr
		self.agent_in_q = agent_in_q
		self.agent_out_q = agent_out_q
		self.ldap = None

	def get_effective_memberships(self, membership_attr):
		try:
			for sid in self.ldap.get_tokengroups(membership_attr['dn']):
				s = JackDawTokenGroup()
				s.cn = membership_attr['cn']
				s.dn = membership_attr['dn']
				s.guid = membership_attr['guid']
				s.sid = membership_attr['sid']
				s.member_sid = sid
				s.is_user = True if membership_attr['type'] == 'user' else False
				s.is_group = True if membership_attr['type'] == 'group' else False
				s.is_machine = True if membership_attr['type'] == 'machine' else False
				self.agent_out_q.put((LDAPAgentCommand.MEMBERSHIP, s))
		except Exception as e:
			self.agent_out_q.put((LDAPAgentCommand.EXCEPTION, str(traceback.format_exc())))
		finally:
			self.agent_out_q.put((LDAPAgentCommand.MEMBERSHIPS_FINISHED, None))

	def enumerate_spnservices(self):
		pass

	def enumerate_machine(self, machine):
		pass
		
	def get_all_spnservices(self):
		try:
			ldap_filter = r'(&(sAMAccountType=805306369))'
			attributes = ['sAMAccountName', 'servicePrincipalName']
			
			for entry in self.ldap.pagedsearch(ldap_filter, attributes):
				for spn in entry['attributes']['servicePrincipalName']:			
					port = None
					service, t = spn.rsplit('/',1)
					m = t.find(':')
					if m != -1:
						computername, port = spn.rsplit(':',1)
					else:
						computername = t
						
					s = JackDawSPNService()
					s.computername = computername
					s.service = service
					s.port = port
					self.agent_out_q.put((LDAPAgentCommand.SPNSERVICE, s))
		except Exception as e:
			self.agent_out_q.put((LDAPAgentCommand.EXCEPTION, str(traceback.format_exc())))
		finally:
			self.agent_out_q.put((LDAPAgentCommand.SPNSERVICES_FINISHED, None))

	def get_all_users(self):
		try:
			for user in self.ldap.get_all_user_objects():
				#TODO: fix this ugly stuff here...
				if user.sAMAccountName[-1] == "$":
					continue
				self.agent_out_q.put((LDAPAgentCommand.USER, JackDawADUser.from_aduser(user)))
		except Exception as e:
			self.agent_out_q.put((LDAPAgentCommand.EXCEPTION, str(traceback.format_exc())))
		finally:
			self.agent_out_q.put((LDAPAgentCommand.USERS_FINISHED, None))

	def get_all_groups(self):
		try:
			for group in self.ldap.get_all_groups():
				self.agent_out_q.put((LDAPAgentCommand.GROUP, JackDawADGroup.from_dict(group.to_dict())))
		except Exception as e:
			self.agent_out_q.put((LDAPAgentCommand.EXCEPTION, str(traceback.format_exc())))
		finally:
			self.agent_out_q.put((LDAPAgentCommand.GROUPS_FINISHED, None))


	def get_all_machines(self):
		try:
			for machine in self.ldap.get_all_machine_objects():
				self.agent_out_q.put((LDAPAgentCommand.MACHINE, JackDawADMachine.from_adcomp(machine)))
		except Exception as e:
			self.agent_out_q.put((LDAPAgentCommand.EXCEPTION, str(traceback.format_exc())))
		finally:
			self.agent_out_q.put((LDAPAgentCommand.MACHINES_FINISHED, None))
	
	def get_all_ous(self):
		try:
			for ou in self.ldap.get_all_ous():
				self.agent_out_q.put((LDAPAgentCommand.OU, JackDawADOU.from_adou(ou)))
		except Exception as e:
			self.agent_out_q.put((LDAPAgentCommand.EXCEPTION, str(traceback.format_exc())))
		finally:
			self.agent_out_q.put((LDAPAgentCommand.OUS_FINISHED, None))

	def get_domain_info(self):
		try:
			info = self.ldap.get_ad_info()
			adinfo = JackDawADInfo.from_dict(info.to_dict())
			self.agent_out_q.put((LDAPAgentCommand.DOMAININFO, adinfo))
		except Exception as e:
			self.agent_out_q.put((LDAPAgentCommand.EXCEPTION, str(traceback.format_exc())))
		finally:
			self.agent_out_q.put((LDAPAgentCommand.DOMAININFO_FINISHED, None))

	def get_sds(self, data):
		try:
			dn = data['dn']
			obj_type = data['obj_type']
			for sd in self.ldap.get_objectacl_by_dn(dn):
				if not sd.nTSecurityDescriptor or not sd.nTSecurityDescriptor.Dacl:
					return
				self.agent_out_q.put((LDAPAgentCommand.SD, {'sd':sd, 'obj_type': obj_type}))
		
		except Exception as e:
			self.agent_out_q.put((LDAPAgentCommand.EXCEPTION, str(traceback.format_exc())))
		finally:
			self.agent_out_q.put((LDAPAgentCommand.SDS_FINISHED, None))

	def setup(self):
		try:
			self.ldap = self.ldap_mgr.get_connection()
			self.ldap.connect()
			return True
		except Exception as e:
			self.agent_out_q.put((LDAPAgentCommand.EXCEPTION, str(traceback.format_exc())))
			return False

	def run(self):
		res = self.setup()
		#print('agent setup res: %s' % res)
		if res is False:
			return
		while True:
			res = self.agent_in_q.get()
			#print('Got new job! %s' % res)
			if res is None:
				return
			
			if res.command == LDAPAgentCommand.DOMAININFO:
				self.get_domain_info()
			elif res.command == LDAPAgentCommand.USERS:
				self.get_all_users()
			elif res.command == LDAPAgentCommand.MACHINES:
				self.get_all_machines()
			elif res.command == LDAPAgentCommand.GROUPS:
				self.get_all_groups()
			elif res.command == LDAPAgentCommand.OUS:
				self.get_all_ous()
			elif res.command == LDAPAgentCommand.SPNSERVICES:
				self.get_all_spnservices()
			elif res.command == LDAPAgentCommand.MEMBERSHIPS:
				self.get_effective_memberships(res.data)
			elif res.command == LDAPAgentCommand.SDS:
				self.get_sds(res.data)

class LDAPEnumeratorManager:
	def __init__(self, db_conn, ldam_mgr, agent_cnt = 5):
		self.db_conn = db_conn
		self.ldam_mgr = ldam_mgr

		self.session = None

		self.agent_in_q = multiprocessing.Queue()
		self.agent_out_q = multiprocessing.Queue()
		self.agents = []
		self.agent_cnt = agent_cnt
		self.ad_id = None

		self.user_ctr = 0
		self.machine_ctr = 0
		self.ou_ctr = 0
		self.group_ctr = 0
		self.sd_ctr = 0
		self.spn_ctr = 0
		self.member_ctr = 0
		self.domaininfo_ctr = 0

		self.user_finish_ctr = 0
		self.machine_finish_ctr = 0
		self.ou_finish_ctr = 0
		self.group_finish_ctr = 0
		self.sd_finish_ctr = 0
		self.spn_finish_ctr = 0
		self.member_finish_ctr = 0
		self.domaininfo_finish_ctr = 0


	@staticmethod
	def spn_to_account(spn):
		if spn.find('/') != -1:
			return spn.rsplit('/')[1].upper() + '$'
	
	def setup(self):
		logger.info('mgr setup')
		self.session = get_session(self.db_conn)
		for _ in range(self.agent_cnt):
			agent = LDAPEnumeratorAgent(self.ldam_mgr, self.agent_in_q, self.agent_out_q)
			agent.daemon = True
			agent.start()
			self.agents.append(agent)

	def enum_domain(self, info):
		#print('Got domain!')
		self.session.add(info)
		self.session.commit()
		self.session.refresh(info)
		self.ad_id = info.id

		self.user_ctr += 1
		job = LDAPAgentJob(LDAPAgentCommand.USERS, self.ad_id)
		self.agent_in_q.put(job)

		self.machine_ctr += 1
		job = LDAPAgentJob(LDAPAgentCommand.MACHINES, self.ad_id)
		self.agent_in_q.put(job)

		self.group_ctr += 1
		job = LDAPAgentJob(LDAPAgentCommand.GROUPS, self.ad_id)
		self.agent_in_q.put(job)

		self.ou_ctr += 1
		job = LDAPAgentJob(LDAPAgentCommand.OUS, self.ad_id)
		self.agent_in_q.put(job)

		self.spn_ctr += 1
		job = LDAPAgentJob(LDAPAgentCommand.SPNSERVICES, self.ad_id)
		self.agent_in_q.put(job)


	def enum_machine(self, machine):
		#print('Got machine object!')
		machine.ad_id = self.ad_id
		self.session.add(machine)
		self.session.commit()
		self.session.refresh(machine)
		
		for spn in getattr(machine,'allowedtodelegateto',[]):
			con = JackDawMachineConstrainedDelegation()
			con.spn = spn
			con.targetaccount = LDAPEnumeratorManager.spn_to_account(spn)
			machine.allowedtodelegateto.append(con)
		
		self.session.commit()

		membership_attr = {
			'dn'  : str(machine.dn),
			'cn'  : str(machine.cn),
			'guid': str(machine.objectGUID),
			'sid' : str(machine.objectSid),
			'type': 'machine'
		}

		self.member_ctr += 1
		job = LDAPAgentJob(LDAPAgentCommand.MEMBERSHIPS, membership_attr)
		self.agent_in_q.put(job)
		
		self.sd_ctr += 1
		job = LDAPAgentJob(LDAPAgentCommand.SDS, {'dn' : machine.dn, 'obj_type': 'machine' })
		self.agent_in_q.put(job)		

	def enum_user(self, user):
		user.ad_id = self.ad_id
		self.session.add(user)
		self.session.commit()
		self.session.refresh(user)

		for spn in getattr(user,'allowedtodelegateto',[]):
			con = JackDawUserConstrainedDelegation()
			con.spn = spn
			con.targetaccount = LDAPEnumeratorManager.spn_to_account(spn)
			user.allowedtodelegateto.append(con)
		
		self.session.commit()

		membership_attr = {
			'dn'  : str(user.dn),
			'cn'  : str(user.cn),
			'guid': str(user.objectGUID),
			'sid' : str(user.objectSid),
			'type': 'user'
		}

		self.member_ctr += 1
		job = LDAPAgentJob(LDAPAgentCommand.MEMBERSHIPS, membership_attr)
		self.agent_in_q.put(job)

		self.sd_ctr += 1
		job = LDAPAgentJob(LDAPAgentCommand.SDS, {'dn' : user.dn, 'obj_type': 'user' })
		self.agent_in_q.put(job)

	def enum_group(self, group):
		group.ad_id = self.ad_id
		self.session.add(group)
		self.session.commit()
		
		membership_attr = {
			'dn'  : str(group.dn),
			'cn'  : str(group.cn),
			'guid': str(group.guid),
			'sid' : str(group.sid),
			'type': 'group'
		}
		
		self.member_ctr += 1
		job = LDAPAgentJob(LDAPAgentCommand.MEMBERSHIPS, membership_attr)
		self.agent_in_q.put(job)

		self.sd_ctr += 1
		job = LDAPAgentJob(LDAPAgentCommand.SDS, {'dn' : group.dn, 'obj_type': 'group' })
		self.agent_in_q.put(job)

	def enum_ou(self, ou):
		ou.ad_id = self.ad_id
		self.session.add(ou)
		self.session.commit()
		
		self.sd_ctr += 1
		job = LDAPAgentJob(LDAPAgentCommand.SDS, {'dn' : ou.dn, 'obj_type': 'ou' })
		self.agent_in_q.put(job)

	def store_spnservice(self, spn):
		#print('Got SPNSERVICE!')
		spn.ad_id = self.ad_id
		self.session.add(spn)
		self.session.commit()


	def store_membership(self, res):
		#print('Got membership object!')
		res.ad_id = self.ad_id
		self.session.add(res)
		self.session.commit()

	def store_sd(self, data):
		#print('Got SD object!')
		sd = data['sd']
		obj_type = data['obj_type']
		order_ctr = 0
		for ace in sd.nTSecurityDescriptor.Dacl.aces:
			acl = JackDawADDACL()
			acl.ad_id = self.ad_id
			acl.object_type = obj_type
			acl.object_type_guid = OBJECTTYPE_GUID_MAP.get(obj_type)
			acl.owner_sid = str(sd.nTSecurityDescriptor.Owner)
			acl.group_sid = str(sd.nTSecurityDescriptor.Group)
			acl.ace_order = order_ctr
			
			order_ctr += 1
			acl.guid = str(sd.objectGUID)
			if sd.objectSid:
				acl.sid = str(sd.objectSid)
			if sd.cn:
				acl.cn = sd.cn
			if sd.distinguishedName:
				acl.dn = str(sd.distinguishedName)
			acl.sd_control = sd.nTSecurityDescriptor.Control
			
			acl.ace_type = ace.Header.AceType.name
			acl.ace_mask = ace.Mask
			t = getattr(ace,'ObjectType', None)
			if t:
				acl.ace_objecttype = str(t)
			
			t = getattr(ace,'InheritedObjectType', None)
			if t:
				acl.ace_inheritedobjecttype = str(t)
				
			true_attr, false_attr = JackDawADDACL.mask2attr(ace.Mask)
			
			for attr in true_attr:	
				setattr(acl, attr, True)
			for attr in false_attr:	
				setattr(acl, attr, False)
				
			true_attr, false_attr = JackDawADDACL.hdrflag2attr(ace.Header.AceFlags)
			
			for attr in true_attr:	
				setattr(acl, attr, True)
			for attr in false_attr:	
				setattr(acl, attr, False)
			
			acl.ace_sid = str(ace.Sid)
			self.session.add(acl)
		
		self.session.commit()

	def check_status(self):
		#print('user')
		#print(self.user_ctr)
		#print(self.user_finish_ctr)
		#
		#print('machine')
		#print(self.machine_ctr)
		#print(self.machine_finish_ctr)
		#
		#print('ou')
		#print(self.ou_ctr)
		#print(self.ou_finish_ctr)
		#
		#print('group')
		#print(self.group_ctr)
		#print(self.group_finish_ctr)
		#
		#print('sd')
		#print(self.sd_ctr)
		#print(self.sd_finish_ctr)
		#
		#print('spn')
		#print(self.spn_ctr)
		#print(self.spn_finish_ctr)
		#
		#print('member')
		#print(self.member_ctr)
		#print(self.member_finish_ctr)
		#
		#print('domain')
		#print(self.domaininfo_ctr)
		#print(self.domaininfo_finish_ctr)

		if self.user_ctr == self.user_finish_ctr \
			and self.machine_ctr == self.machine_finish_ctr\
			and self.ou_ctr == self.ou_finish_ctr\
			and self.group_ctr == self.group_finish_ctr\
			and self.sd_ctr == self.sd_finish_ctr\
			and self.spn_ctr == self.spn_finish_ctr\
			and self.member_ctr == self.member_finish_ctr\
			and self.domaininfo_ctr == self.domaininfo_finish_ctr:
			return True
		return False

	def stop_agents(self):
		logger.info('mgr stop')
		self.session.commit()
		self.session.close()
		for _ in self.agents:
			self.agent_in_q.put(None)
		for agent in self.agents:
			agent.join()
		logger.info('stopped all agents!')

	def run(self):
		self.setup()
		logger.info('setup finished!')

		self.domaininfo_ctr += 1
		job = LDAPAgentJob(LDAPAgentCommand.DOMAININFO, None)
		self.agent_in_q.put(job)

		while True:
			res = self.agent_out_q.get()
			#print(res)
			res_type, res = res
			if res_type == LDAPAgentCommand.DOMAININFO:
				self.enum_domain(res)
			
			elif res_type == LDAPAgentCommand.USER:
				self.enum_user(res)

			elif res_type == LDAPAgentCommand.MACHINE:
				self.enum_machine(res)

			elif res_type == LDAPAgentCommand.SPNSERVICE:
				self.store_spnservice(res)

			elif res_type == LDAPAgentCommand.GROUP:
				self.enum_group(res)

			elif res_type == LDAPAgentCommand.OU:
				self.enum_ou(res)
			
			elif res_type == LDAPAgentCommand.SD:
				self.store_sd(res)
			
			elif res_type == LDAPAgentCommand.MEMBERSHIP:
				self.store_membership(res)

			elif res_type == LDAPAgentCommand.EXCEPTION:
				logger.warning(res)

			elif res_type == LDAPAgentCommand.SPNSERVICES_FINISHED:
				self.spn_finish_ctr += 1
			elif res_type == LDAPAgentCommand.USERS_FINISHED:
				self.user_finish_ctr += 1
			elif res_type == LDAPAgentCommand.MACHINES_FINISHED:
				self.machine_finish_ctr += 1
			elif res_type == LDAPAgentCommand.OUS_FINISHED:
				self.ou_finish_ctr += 1
			elif res_type == LDAPAgentCommand.GROUPS_FINISHED:
				self.group_finish_ctr += 1
			elif res_type == LDAPAgentCommand.MEMBERSHIPS_FINISHED:
				self.member_finish_ctr += 1
			elif res_type == LDAPAgentCommand.SDS_FINISHED:
				self.sd_finish_ctr += 1
			elif res_type == LDAPAgentCommand.DOMAININFO_FINISHED:
				self.domaininfo_finish_ctr += 1

			if self.check_status() == True:
				break
		
		self.stop_agents()
		return self.ad_id

		
if __name__ == '__main__':
	from msldap.commons.url import MSLDAPURLDecoder

	import sys
	sql = sys.argv[1]
	ldap_conn_url = sys.argv[2]

	print(sql)
	print(ldap_conn_url)
	
	ldap_mgr = MSLDAPURLDecoder(ldap_conn_url)

	mgr = LDAPEnumeratorManager(sql, ldap_mgr)
	mgr.run()