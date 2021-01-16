import zipfile
import json
import codecs
import pprint
import datetime
import traceback

import platform
from tqdm import tqdm
if platform.system() == 'Emscripten':
	tqdm.monitor_interval = 0

from jackdaw import logger
from jackdaw.dbmodel import *
from jackdaw.dbmodel.adinfo import ADInfo
from jackdaw.dbmodel.adcomp import Machine
from jackdaw.dbmodel.aduser import ADUser
from jackdaw.dbmodel.adgroup import Group
from jackdaw.dbmodel.adou import ADOU


def pretty(d, indent=0):
   for key, value in d.items():
      print('\t' * indent + str(key))
      if isinstance(value, dict):
        pretty(value, indent+1)
      else:
        print('\t' * (indent+1) + str(value))

def convert_to_dt(s):
	if not isinstance(s, int):
		if s is None or s.lower() == 'none':
			return None
		if isinstance(s, str):
			if s.startswith('TMSTMP-') is True:
				s = s.replace('TMSTMP-', '')
			elif s == 'Never':
				s = -1
		try:
			s = int(s)
		except:
			logger.debug('Datetime conversion failed for value %s' % s)
			return None
	
	return datetime.datetime.utcfromtimestamp(s)

same_labels = {
	'WriteOwner' : 1,
	'Owner' : 1,
	'WriteDacl' : 1,
	'GenericWrite' : 1,
	'AddMember' : 1,
	'GetChanges' : 1,
	'ReadLAPSPassword' : 1,
	'User-Force-Change-Password' : 1,
	#'' : 1,
	#'' : 1,
	#'' : 1,
	#'' : 1,

}


class BHImport:
	def __init__(self, db_conn = None, db_session = None):
		self.debug = False
		self.graphid = None
		self.zipfile = None
		self.files = None
		self.db_conn = db_conn
		self.db_session = db_session
		self.bloodhound_version = '2'
		self.acls = []
		self.bh_version_2_user_spns = []

		self.is_zip = False
		self.fd = {}
		self.ads = {}
		self.adn = {} #name -> ad_id

		#self.setup_db()
		self.sid_id_cache = {} #sid - > id
		self.sid_name_cache = {} #oname -> sid v2
		self.edges = []
		self.spns = []
		self.disable_print_progress = True if platform.system() == 'Emscripten' else False


	def setup_db(self):
		if self.db_session is None:
			self.db_session = get_session(self.db_conn)

	@staticmethod
	def member_type_lookup(membertype):
		mt = membertype.lower()
		if mt == 'computer':
			return 'machine'
		return mt

	@staticmethod
	def convert_label(rightname):
		if rightname in same_labels:
			return rightname
		elif rightname == 'GenericAll':
			return 'GenericALL'
		elif rightname == 'All': #this only appears in the extendedrights
			return 'ExtendedAll'
		elif rightname == 'GetChangesAll':
			return 'GetChangesALL'
		
		logger.debug('Unknown label! %s' % rightname)
		return 'unknown'
	
	@staticmethod
	def convert_otype(otype):
		ot = otype.lower()
		if ot == 'group':
			return 'group'
		elif ot == 'computer':
			return 'machine'
		elif ot == 'user':
			return 'user'
		elif ot == 'trust':
			return 'trust'
		elif ot == 'domain':
			return 'domain'
		elif ot == 'ou':
			return 'ou'
		elif ot == 'gpo':
			return 'gpo'
		elif ot == 'unknown':
			return 'unknown'
		else:
			logger.debug('[BHIMPORT] Unknown otype! %s' % otype)
		return 'unknown'

	@staticmethod
	def process_spn(spn, owner_sid):
		port = None
		service_name = None
		service_class, t = spn.split('/',1)
		m = t.find(':')
		if m != -1:
			computername, port = t.rsplit(':',1)
			if port.find('/') != -1:
				port, service_name = port.rsplit('/',1)
		else:
			computername = t
			if computername.find('/') != -1:
				computername, service_name = computername.rsplit('/',1)

		s = SPNService()
		s.owner_sid = owner_sid
		s.computername = computername
		s.service_class = service_class
		s.service_name = service_name
		if port is not None:
			s.port = str(port)
		return s

	def breakup_groupsid(self, sid, ad_id):
		is_domainsid = True
		real_sid = sid
		machine_sid = None
		pattern_loc = sid.find('S-1-')
		if pattern_loc == -1:
			return sid, None, sid, True
			#raise Exception('Cant parse group sid! %s' % (sid,))
		elif pattern_loc != 0:
			real_sid = sid[pattern_loc:]
			sub_name = sid[:pattern_loc-1]
			res_domain = self.db_session.query(ADInfo).get(ad_id)
			if res_domain is None:
				raise Exception('breakup_groupsid Cound not find domain with  %s' % ad_id)
				#print(ad_id)
				#print(sid)
				#input()
			if res_domain is None or res_domain.name.lower() != sub_name.lower():
				res_machine = self.db_session.query(Machine).filter_by(name = sub_name).filter(Machine.ad_id == ad_id).first()
				if res_machine is None:
					raise Exception('breakup_groupsid Cound not find machine for name %s' % sub_name)
					#print(sid)
					#print(sub_name)
					#print(res_domain.name)
					#print('rs %s ' % real_sid)
					#input()
				else:
					is_domainsid = False
					machine_sid = res_machine.objectSid
			else:
				machine_sid = res_domain.objectSid
		
		oid = real_sid
		if machine_sid is not None:
			oid = machine_sid + '|' + real_sid
		
		return real_sid, machine_sid, oid, is_domainsid

	def sid_to_id(self, osid, objtype, adid):
		# objtype unknown????!!!
		sid, machine_sid, oid, is_domainsid = self.breakup_groupsid(osid, adid)
		if is_domainsid is False:
			logger.debug('[BHIMPORT] Not domainsid! %s ' % osid)

		if sid in self.sid_id_cache:
			return self.sid_id_cache[sid]

		res = self.db_session.query(EdgeLookup).filter_by(oid = sid).filter(EdgeLookup.ad_id == adid).first()
		if res is None:
			edgeinfo = EdgeLookup(adid, sid, objtype)
			self.db_session.add(edgeinfo)
			self.db_session.commit()
			self.db_session.refresh(edgeinfo)
			if objtype != 'unknown':
				self.sid_id_cache[sid] = edgeinfo.id
			return edgeinfo.id
		else:
			# this should not happen normally...
			if res.otype == 'unknown' and objtype != 'unknown':
				#print('replacing unknown with %s' % objtype)
				res.otype = objtype
				self.db_session.add(res)
				self.db_session.commit()

		self.sid_id_cache[sid] = res.id
		return res.id
	
	def insert_edges(self):
		for srcsid, srctype, dstsid, dsttype, label, adid in tqdm(self.edges, desc='Edges   ', total=len(self.edges), disable = self.disable_print_progress):
			dst = self.sid_to_id(dstsid, dsttype, adid)
			src = self.sid_to_id(srcsid, srctype, adid)
			edge = Edge(adid, self.graphid, src, dst, label)
			self.db_session.add(edge)
		
		self.db_session.commit()

	def add_edge(self, srcsid, srctype, dstsid, dsttype, label, adid):
		self.edges.append((srcsid, srctype, dstsid, dsttype, label, adid))
		

	def sid_name_lookup_v2(self, oname, otype, adid):
		if oname in self.sid_name_cache:
			return self.sid_name_cache[oname]
		name = oname.split('@',1)[0]
		if otype.lower() == 'group':
			res = self.db_session.query(Group).filter_by(name=name).filter(Group.ad_id == adid).first()
			if res is None:
				raise Exception('Cant find group! %s' % oname)
			self.sid_name_cache[oname] = res.objectSid
			return res.objectSid
		elif otype.lower() == 'user':
			res = self.db_session.query(ADUser).filter_by(name=name).filter(ADUser.ad_id == adid).first()
			if res is None:
				raise Exception('Cant find user! %s' % oname)
			self.sid_name_cache[oname] = res.objectSid
			return res.objectSid
		elif otype.lower() == 'computer':
			res = self.db_session.query(Machine).filter_by(dNSHostName=name.upper()).filter(Machine.ad_id == adid).first()
			if res is None:
				raise Exception('Cant find machine! %s' % oname)
			self.sid_name_cache[oname] = res.objectSid
			return res.objectSid
		else:
			raise Exception('Could not find oname %s otype %s in adid %s' % (oname, otype, adid))
			

	def insert_all_acls(self):
		if self.bloodhound_version == '2':
			for dstsid, dsttype, acl, adid in tqdm(self.acls, desc='ACLs    ', total=len(self.acls), disable=self.disable_print_progress):
				for ace in acl:
					try:
						if self.debug is True:
							print(ace)
							input()
						psid = self.sid_name_lookup_v2(ace['PrincipalName'], ace['PrincipalType'], adid)
						dst = self.sid_to_id(dstsid, dsttype, adid)
						src = self.sid_to_id(psid, BHImport.convert_otype(ace['PrincipalType']), adid)
						
						if ace['RightName'] == 'ExtendedRight' or ace['RightName'] == 'WriteProperty':
							label = BHImport.convert_label(ace['AceType'])
						else:
							label = BHImport.convert_label(ace['RightName'])
						
						edge = Edge(adid, self.graphid, src, dst, label)
						self.db_session.add(edge)
					except Exception as e:
						logger.debug('[BHIMPORT] Skipping ace %s Error: %s' % (ace, e))
			self.db_session.commit()
		
		else:
			for dstsid, dsttype, acl, adid in tqdm(self.acls, desc='ACLs    ', total=len(self.acls), disable=self.disable_print_progress):
				for ace in acl:
					if self.debug is True:
						print(ace)
						input()
					dst = self.sid_to_id(dstsid, dsttype, adid)
					src = self.sid_to_id(ace['PrincipalSID'], BHImport.convert_otype(ace['PrincipalType']), adid)
					if ace['RightName'] == 'ExtendedRight' or ace['RightName'] == 'WriteProperty':			
						label = BHImport.convert_label(ace['AceType'])
					else:
						label = BHImport.convert_label(ace['RightName'])
					
					#self.add_edge()
					edge = Edge(adid, self.graphid, src, dst, label)
					self.db_session.add(edge)

	def insert_spns(self):
		if self.bloodhound_version == '2':
			for sid, ad_id, spns in self.spns:
				for spn in spns:
					s = BHImport.process_spn(spn, sid)
					self.db_session.add(s)
					if s.service_class == 'MSSQLSvc':
						res = self.db_session.query(Machine).filter_by(dNSHostName = s.computername.upper()).filter(Machine.ad_id == ad_id).first()
						if res is not None:
							self.add_edge(sid, 'user', res.objectSid, 'machine', 'sqladmin', ad_id)
						else:
							logger.debug('[BHIMPORT] sqlaldmin add edge cant find machine %s' % s.computername)

		else:
			for user_sid, adid, spns in self.spns:
				for spn in spns:
					s = BHImport.process_spn(spn, user_sid)
					self.db_session.add(s)
					if s.service_class == 'MSSQLSvc':
						res = self.db_session.query(Machine).filter_by(dNSHostName = s.computername.upper()).filter(Machine.ad_id == adid).first()
						if res is not None:
							self.add_edge(user_sid, 'user', res.objectSid, 'machine', 'sqladmin', adid)
						else:
							logger.debug('[BHIMPORT] Cant find machine %s' % s.computername)
		
	def insert_acl(self, dstsid, dsttype,  acl, adid):
		self.acls.append((dstsid, dsttype,  acl, adid))

	def import_machines(self):
		logger.debug('[BHIMPORT] Importing machines')
		meta = self.get_file('computers')['meta']
		total = meta['count']
		for machine in tqdm(self.get_file('computers')['computers'], desc='Machines', total=total, disable=self.disable_print_progress):
			if self.debug is True:
				pretty(machine)
				input()
			try:
				if self.bloodhound_version == '2':
					m = Machine()
					m.ad_id = self.adn[machine['Properties']['domain']]
					#m.dn = machine['Properties']['distinguishedname']
					m.canLogon = machine['Properties'].get('enabled')
					m.lastLogonTimestamp = convert_to_dt(machine['Properties'].get('lastlogontimestamp'))
					m.pwdLastSet = convert_to_dt(machine['Properties'].get('pwdlastset'))
					m.operatingSystem = machine['Properties'].get('operatingsystem')
					m.dNSHostName = machine['Name']
					m.cn = machine['Name'].split('.',1)[0]
					m.name = m.cn
					m.sAMAccountName = machine['Name'].split('.', 1)[0] + '$'
					m.objectSid = machine['Properties']['objectsid']
					m.canLogon = machine['Properties'].get('enabled')
					m.UAC_TRUSTED_FOR_DELEGATION = machine['Properties'].get('unconstraineddelegation')
					m.description = machine['Properties'].get('description')
					if machine['Properties'].get('highvalue') is True:
						hvt = ADObjProps(self.graphid, m.objectSid, 'HVT')
						self.db_session.add(hvt)

					#m.operatingSystemVersion  = machine['Properties']['operatingsystem']

					#not importing [Properties][haslaps] [Properties][serviceprincipalnames] 
					# [AllowedToDelegate] [AllowedToAct]

				else:
					m = Machine()
					m.ad_id = self.adn[machine['Properties']['domain']]
					m.dn = machine['Properties']['distinguishedname']
					m.canLogon = machine['Properties']['enabled']
					m.lastLogonTimestamp = convert_to_dt(machine['Properties']['lastlogontimestamp'])
					m.pwdLastSet = convert_to_dt(machine['Properties']['pwdlastset'])
					m.operatingSystem = machine['Properties']['operatingsystem']
					m.dNSHostName = machine['Properties']['name']
					m.cn = machine['Properties']['name'].split('.',1)[0]
					m.sAMAccountName = machine['Properties']['name'].split('.', 1)[0] + '$'
					m.objectSid = machine['Properties']['objectid']
					m.description = machine['Properties']['description']
					m.UAC_TRUSTED_FOR_DELEGATION = machine['Properties'].get('unconstraineddelegation')
					#m.operatingSystemVersion  = machine['Properties']['operatingsystem']

					if machine['Properties'].get('highvalue') is True:
						hvt = ADObjProps(self.graphid, m.objectSid, 'HVT')
						self.db_session.add(hvt)

					if 'serviceprincipalnames' in machine['Properties']:
						if len(machine['Properties']['serviceprincipalnames']) > 0:
							m.servicePrincipalName = '|'.join(machine['Properties']['serviceprincipalnames'])
						for spn in machine['Properties']['serviceprincipalnames']:
							s = BHImport.process_spn(spn, m.objectSid)
							self.db_session.add(s)

					if 'Sessions' in machine:
						for session in machine['Sessions']:
							self.add_edge(session['UserId'], 'user', session['ComputerId'], 'machine', 'hasSession', m.ad_id)
							self.add_edge(session['ComputerId'], 'machine', session['UserId'], 'user', 'hasSession', m.ad_id)
							self.db_session.add(s)

					#not importing [Properties][haslaps] [AllowedToDelegate] [AllowedToAct]

				if 'LocalAdmins' in machine and machine['LocalAdmins'] is not None:
					for localadmin in machine['LocalAdmins']:
						if self.bloodhound_version == '2':
							s = LocalGroup()
							s.ad_id = m.ad_id
							s.machine_sid = m.objectSid
							s.sid = self.sid_name_lookup_v2(localadmin['Name'], localadmin['Type'],  m.ad_id)
							s.groupname = 'Administrators'
							self.db_session.add(s)
							self.add_edge(s.sid, BHImport.convert_otype(localadmin['Type']), s.machine_sid, 'machine', 'adminTo', m.ad_id)

						else:
							s = LocalGroup()
							s.ad_id = m.ad_id
							s.machine_sid = m.objectSid
							s.sid = localadmin['MemberId']
							s.groupname = 'Administrators'
							self.db_session.add(s)
							self.add_edge(s.sid, BHImport.convert_otype(localadmin['MemberType']), s.machine_sid, 'machine', 'adminTo', m.ad_id)

				if 'DcomUsers' in machine and machine['DcomUsers'] is not None:
					for localadmin in machine['DcomUsers']:
						if self.bloodhound_version == '2':
							s = LocalGroup()
							s.ad_id = m.ad_id
							s.machine_sid = m.objectSid
							s.sid = self.sid_name_lookup_v2(localadmin['Name'], localadmin['Type'],  m.ad_id)
							s.groupname = 'Distributed COM Users'
							self.db_session.add(s)
							self.add_edge(s.sid, BHImport.convert_otype(localadmin['Type']), s.machine_sid, 'machine', 'executeDCOM', m.ad_id)
						else:
							s = LocalGroup()
							s.ad_id = m.ad_id
							s.machine_sid = m.objectSid
							s.sid = localadmin['MemberId']
							s.groupname = 'Distributed COM Users'
							self.db_session.add(s)
							self.add_edge(s.sid, BHImport.convert_otype(localadmin['MemberType']), s.machine_sid, 'machine', 'executeDCOM', m.ad_id)

				if 'RemoteDesktopUsers' in machine and machine['RemoteDesktopUsers'] is not None:
					for localadmin in machine['RemoteDesktopUsers']:
						if self.bloodhound_version == '2':
							s = LocalGroup()
							s.ad_id = m.ad_id
							s.machine_sid = m.objectSid
							s.sid = self.sid_name_lookup_v2(localadmin['Name'], localadmin['Type'],  m.ad_id)
							s.groupname = 'Remote Desktop Users'
							self.db_session.add(s)
							self.add_edge(s.sid, BHImport.convert_otype(localadmin['Type']), s.machine_sid, 'machine', 'canRDP', m.ad_id)

						else:
							s = LocalGroup()
							s.ad_id = m.ad_id
							s.machine_sid = m.objectSid
							s.sid = localadmin['MemberId']
							s.groupname = 'Remote Desktop Users'
							self.db_session.add(s)
							self.add_edge(s.sid, BHImport.convert_otype(localadmin['MemberType']), s.machine_sid, 'machine', 'canRDP', m.ad_id)

				if 'PSRemoteUsers' in machine:
					for localadmin in machine['PSRemoteUsers']:
						if self.bloodhound_version == '2':
							s = LocalGroup()
							s.ad_id = m.ad_id
							s.machine_sid = m.objectSid
							s.sid = self.sid_name_lookup_v2(localadmin['Name'], localadmin['Type'],  m.ad_id)
							s.groupname = 'Remote Management Users'
							self.db_session.add(s)
							self.add_edge(s.sid, BHImport.convert_otype(localadmin['Type']), s.machine_sid, 'machine', 'psremote', m.ad_id)
						else:
							s = LocalGroup()
							s.ad_id = m.ad_id
							s.machine_sid = m.objectSid
							s.sid = localadmin['MemberId']
							s.groupname = 'Remote Management Users'
							self.db_session.add(s)
							self.add_edge(s.sid, BHImport.convert_otype(localadmin['MemberType']), s.machine_sid, 'machine', 'psremote', m.ad_id)
			
				self.db_session.add(m)
				edgeinfo = EdgeLookup(m.ad_id, m.objectSid, 'machine')
				self.db_session.add(edgeinfo)
				#self.db_session.commit()

				if machine['Aces'] is not None:
					self.insert_acl(m.objectSid, 'machine', machine['Aces'], m.ad_id)
			
			except Exception as e:
				logger.debug('[BHIMPORT] Failed importing machine %s Reason: %s' % (machine, e))
				continue

		self.db_session.commit()


	def import_users(self):
		logger.debug('[BHIMPORT] Importing users')		
		meta = self.get_file('users')['meta']
		total = meta['count']
		
		for user in tqdm(self.get_file('users')['users'], desc='Users   ', total=total, disable=self.disable_print_progress):
			try:
				if self.debug is True:
					pretty(user)
					input()
					
				if self.bloodhound_version == '2':
					m = ADUser()
					m.ad_id = self.ads[user['Properties']['objectsid'].rsplit('-',1)[0]]
					m.name = user['Name'].split('@', 1)[0]
					m.sAMAccountName = m.name
					m.objectSid = user['Properties']['objectsid']
					m.canLogon = user['Properties'].get('enabled')
					m.lastLogonTimestamp = convert_to_dt(user['Properties'].get('lastlogontimestamp'))
					m.lastLogon = convert_to_dt(user['Properties'].get('lastlogon'))
					m.pwdLastSet = convert_to_dt(user['Properties'].get('pwdlastset'))
					m.displayName = user['Properties'].get('displayname')
					m.email  = user['Properties'].get('email')
					m.description = user['Properties'].get('description')
					m.UAC_DONT_REQUIRE_PREAUTH = user['Properties'].get('dontreqpreauth')
					m.UAC_PASSWD_NOTREQD = user['Properties'].get('passwordnotreqd')
					m.UAC_TRUSTED_FOR_DELEGATION = user['Properties'].get('unconstraineddelegation')
					m.adminCount = user['Properties'].get('admincount')

					#not importing [Properties][highvalue] [Properties][hasspn] [Properties][title] [Properties][homedirectory] [Properties][userpassword] [Properties][sensitive] [AllowedToDelegate] [SPNTargets]

				else:
					m = ADUser()
					m.ad_id = self.ads[user['Properties']['objectid'].rsplit('-',1)[0]]
					m.dn = user['Properties']['distinguishedname']
					m.name = user['Properties']['name'].split('@', 1)[0]
					m.sAMAccountName = m.name
					m.objectSid = user['Properties']['objectid']
					m.description = user['Properties']['description']
					m.displayName  = user['Properties']['displayname']
					m.email  = user['Properties']['email']
					m.UAC_DONT_REQUIRE_PREAUTH = user['Properties']['dontreqpreauth']
					m.UAC_PASSWD_NOTREQD = user['Properties']['passwordnotreqd']
					m.UAC_TRUSTED_FOR_DELEGATION = user['Properties']['unconstraineddelegation']
					m.canLogon = user['Properties']['enabled']
					if 'pwdneverexpires' in user['Properties']:
						m.UAC_DONT_EXPIRE_PASSWD = user['Properties']['pwdneverexpires']
					m.adminCount = user['Properties']['admincount']
					m.pwdLastSet = convert_to_dt(user['Properties']['pwdlastset'])
					m.lastLogonTimestamp = convert_to_dt(user['Properties']['lastlogontimestamp'])
					m.lastLogon = convert_to_dt(user['Properties']['lastlogon'])
					m.displayName = user['Properties']['displayname']

					#not importing [Properties][highvalue] [Properties][hasspn]  [Properties][sidhistory] [Properties][title] [Properties][homedirectory] [Properties][userpassword] [Properties][sensitive] [HasSIDHistory] [AllowedToDelegate] [SPNTargets]

				if user['Properties'].get('highvalue') is True:
					hvt = ADObjProps(self.graphid, m.objectSid, 'HVT')
					self.db_session.add(hvt)

				if 'serviceprincipalnames' in user['Properties']:
					if len(user['Properties']['serviceprincipalnames']) > 0:
						m.servicePrincipalName = '|'.join(user['Properties']['serviceprincipalnames'])
						self.spns.append((m.objectSid, m.ad_id, user['Properties']['serviceprincipalnames']))

				self.db_session.add(m)
				edgeinfo = EdgeLookup(m.ad_id, m.objectSid, 'user')
				self.db_session.add(edgeinfo)
				#self.db_session.commit()

				if user['Aces'] is not None:
					self.insert_acl(m.objectSid, 'user', user['Aces'], m.ad_id)
				
			except Exception as e:
				logger.debug('[BHIMPORT] Error while processing user %s Reason: %s' % (user,e))
				continue
		self.db_session.commit()
	
	def import_sessions(self):
		logger.debug('[BHIMPORT] Importing sessions')
		meta = self.get_file('sessions')['meta']
		total = meta['count']

		for session in tqdm(self.get_file('sessions')['sessions'], desc='Sessions', total=total, disable=self.disable_print_progress):
			if self.debug is True:
				pprint.pprint(session)
				input()
			try:
				if session['ComputerName'].startswith('['):
					continue
				ad_name = session['UserName'].rsplit('@', 1)[1]
				uname =  session['UserName'].rsplit('@', 1)[0]
	
				qry = self.db_session.query(
					Machine.objectSid
					).filter_by(ad_id = self.adn[ad_name]
					).filter(Machine.dNSHostName == session['ComputerName']
					)
				machine_sid = qry.first()
				
				if machine_sid is None:
					logger.debug('Missing computer! Skipping session %s' % session)
					continue
					#raise Exception('Could not find machine!')
				
				machine_sid = machine_sid[0]

				user_qry = self.db_session.query(
					ADUser.objectSid
					).filter_by(ad_id = self.adn[ad_name]
					).filter(ADUser.sAMAccountName == uname
					)
				user_sid = user_qry.first()
				
				if user_sid is None:
					logger.debug('Missing user! Skipping session %s' % session)
					continue
					#raise Exception('Could not find user!')
				
				user_sid = user_sid[0]
				self.add_edge(machine_sid, 'machine', user_sid, 'user', 'session', self.adn[ad_name])
				self.add_edge(user_sid, 'user', machine_sid, 'machine', 'session', self.adn[ad_name])
			except Exception as e:
				logger.debug('[BHIMPORT] Session import error! Skipping session %s Reason: %s' % (session, e))
				continue
		self.db_session.commit()

	def import_ous(self):
		logger.debug('[BHIMPORT] Importing OUs')
	
		meta = self.get_file('ous')['meta']
		total = meta['count']
		for ou in tqdm(self.get_file('ous')['ous'], desc='OUs     ', total=total, disable=self.disable_print_progress):
			if self.debug is True:
				pprint.pprint(ou)
				input()
			try:
				if self.bloodhound_version == '2':
					ad_name = ou['Properties']['name'].rsplit('@', 1)[1]
					m = ADOU()
					m.ad_id = self.adn[ad_name]
					m.name = ou['Properties']['name'].split('@', 1)[0]
					m.objectGUID = ou['Guid']
					m.description = ou['Properties'].get('description', None)

					if ou['Properties'].get('highvalue') is True:
						hvt = ADObjProps(self.graphid, m.objectGUID, 'HVT')
						self.db_session.add(hvt)

					#not importing [ChildOus] [Properties][blocksinheritance][Computers]

				else:
					ad_name = ou['Properties']['name'].rsplit('@', 1)[1]
					m = ADOU()
					m.ad_id = self.adn[ad_name]
					m.name = ou['Properties']['name'].split('@', 1)[0]
					m.objectGUID = ou['ObjectIdentifier']
					m.description = ou['Properties'].get('description', None)
					m.dn = ou['Properties'].get('distinguishedname', None)

					if ou['Properties'].get('highvalue') is True:
						hvt = ADObjProps(self.graphid, m.objectGUID, 'HVT')
						self.db_session.add(hvt)

					#not importing [ChildOus] [Properties][blocksinheritance] [Users] [RemoteDesktopUsers] [PSRemoteUsers] [LocalAdmins] [Computers] [DcomUsers] [ACLProtected]

				if 'Links' in ou and ou['Links'] is not None:
					for link in ou['Links']:
						#input(link)
						l = Gplink()
						l.ad_id = m.ad_id
						l.ou_guid = m.objectGUID
						if self.bloodhound_version == '2':
							gponame = link['Name'].split('@', 1)[0]
							res = self.db_session.query(GPO).filter_by(name=gponame).filter(GPO.ad_id == m.ad_id).first()
							if res is None:
								logger.debug('Could not insert OU link %s. Reason: could not find GPO %s' % (link, link['Name']))
								continue
							l.gpo_dn = res.objectGUID
						else:
							l.gpo_dn = '{%s}' % link['Guid']
						self.db_session.add(l)

					#not importing [IsEnforced]

				self.db_session.add(m)
				edgeinfo = EdgeLookup(m.ad_id, m.objectGUID, 'ou')
				self.db_session.add(edgeinfo)
				self.db_session.commit()

				if ou['Aces'] is not None:
					self.insert_acl(m.objectGUID, 'ou', ou['Aces'], m.ad_id)
				
			except Exception as e:
				logger.debug('[BHIMPORT] Error while processing OU %s Reason: %s' % (ou,e))
				continue
		self.db_session.commit()
		

	def import_domains(self):
		gi = GraphInfo('bloodhound import')
		
		self.db_session.add(gi)
		self.db_session.commit()
		self.db_session.refresh(gi)
		self.graphid = gi.id
		aces = []

		meta = self.get_file('domains')['meta']
		if 'version' in meta:
			logger.debug('[BHIMPORT] Found version info in file!' )
			self.bloodhound_version = str(meta['version'])
		logger.debug('[BHIMPORT] Selecting bloodhound file version %s' % self.bloodhound_version)
		total = meta['count']
		for domain in tqdm(self.get_file('domains')['domains'], desc='Domains ', total=total, disable=self.disable_print_progress): #['computers']:
			try:
				if self.debug is True:
					pretty(domain)
					input('a')
				di = ADInfo()
				if self.bloodhound_version == '2':
					di.name = domain['Name']
					di.objectSid = domain['Properties']['objectsid']
					di.distinguishedName = 'DC='.join(domain['Name'].split('.'))

					#not importing: [Properties][functionallevel] , [Properties][description], [Links], [Trusts]

				else:
					di.name = domain['Properties']['name']
					di.objectSid = domain['Properties']['objectid']
					di.distinguishedName = domain['Properties']['distinguishedname']

					#not importing: [Properties][functionallevel] , [Properties][description], [ChildOus], [Links], [Trusts]


				self.db_session.add(di)
				self.db_session.commit()
				self.db_session.refresh(di)
				self.ad_id = di.id

				edgeinfo = EdgeLookup(di.id, di.objectSid, 'domain')
				self.db_session.add(edgeinfo)
				self.db_session.commit()

				self.ads[di.objectSid] = di.id
				self.adn[di.name] = di.id

				giad = GraphInfoAD(di.id, self.graphid)
				self.db_session.add(giad)
				self.db_session.commit()
				
				if domain['Aces'] is not None:
					aces.append((di.objectSid, 'domain', domain['Aces'], di.id))
				
			except Exception as e:
				logger.debug('[BHIMPORT] Error while processing domain %s Reason: %s' % (domain,e))
				raise e
		
		for objectSid, ot, aces, adid in aces:
			self.insert_acl(objectSid, ot, aces, adid)

		self.db_session.commit()
		logger.debug('[BHIMPORT] Domain import finished!')

	def import_gpos(self):
		logger.debug('[BHIMPORT] Importing GPOs')
		
		meta = self.get_file('gpos')['meta']
		total = meta['count']

		for gpo in tqdm(self.get_file('gpos')['gpos'], desc='GPOs    ', total=total, disable=self.disable_print_progress):
			if self.debug is True:
				pprint.pprint(gpo)
				input('GPO')
			try:

				if self.bloodhound_version == '2':
					ad_name = gpo['Properties']['domain']
					m = GPO()
					m.ad_id = self.adn[ad_name]
					m.name = gpo['Name'].split('@', 1)[0]
					m.objectGUID = gpo['Guid']
					m.description = gpo['Properties'].get('description')
					m.dn = gpo['Properties'].get('distinguishedname')
					m.path = gpo['Properties'].get('gpcpath')

					if gpo['Properties'].get('highvalue') is True:
						hvt = ADObjProps(self.graphid, m.objectGUID, 'HVT')
						self.db_session.add(hvt)

				else:
					ad_name = gpo['Properties']['domain']
					m = GPO()
					m.ad_id = self.adn[ad_name]
					m.name = gpo['Properties']['name'].split('@', 1)[0]
					m.objectGUID = gpo['ObjectIdentifier']
					m.description = gpo['Properties'].get('description')
					m.dn = gpo['Properties'].get('distinguishedname')
					m.path = gpo['Properties'].get('gpcpath')

					if gpo['Properties'].get('highvalue') is True:
						hvt = ADObjProps(self.graphid, m.objectGUID, 'HVT')
						self.db_session.add(hvt)

				self.db_session.add(m)
				edgeinfo = EdgeLookup(m.ad_id, m.objectGUID, 'gpo')
				self.db_session.add(edgeinfo)
				self.db_session.commit()

				if gpo['Aces'] is not None:
					self.insert_acl(m.objectGUID, 'gpo', gpo['Aces'], m.ad_id)
				
			except Exception as e:
				logger.debug('[BHIMPORT] Error while processing GPO %s Reason: %s' % (gpo, e))
				continue
		
		self.db_session.commit()

	def import_groups(self):
		logger.debug('[BHIMPORT] Importing groups')
		meta = self.get_file('groups')['meta']
		total = meta['count']
		for groups in tqdm(self.get_file('groups')['groups'], desc = 'Groups  ', total=total, disable=self.disable_print_progress):
			if self.debug is True:
				pretty(groups)
				input()
			
			try:
				if self.bloodhound_version == '2':
					ad_name = groups['Name'].rsplit('@', 1)[1]
					m = Group()
					m.ad_id = self.adn[ad_name]
					m.name = groups['Name'].split('@', 1)[0]
					m.sAMAccountName = m.name

					m.objectSid, _, m.oid, is_domainsid = self.breakup_groupsid(groups['Properties']['objectsid'], m.ad_id)
					if is_domainsid is False:
						print('localgroup! %s' % m.oid)
					m.description = groups['Properties'].get('description', None)
					m.adminCount = groups['Properties'].get('admincount')
					
					if groups['Properties'].get('highvalue') is True:
						hvt = ADObjProps(self.graphid, m.objectSid, 'HVT')
						self.db_session.add(hvt)

				else:
					ad_name = groups['Properties']['name'].rsplit('@', 1)[1]
					m = Group()
					m.ad_id = self.adn[ad_name]
					m.name = groups['Properties']['name'].split('@', 1)[0]
					m.sAMAccountName = m.name
					
					m.objectSid, _, m.oid, is_domainsid = self.breakup_groupsid(groups['ObjectIdentifier'], m.ad_id)
					if is_domainsid is False:
						print('localgroup! %s' % m.oid)
					m.description = groups['Properties'].get('description', None)
					m.dn = groups['Properties'].get('distinguishedname')
					m.adminCount = groups['Properties'].get('admincount')

					if groups['Properties'].get('highvalue') is True:
						hvt = ADObjProps(self.graphid, m.objectSid, 'HVT')
						self.db_session.add(hvt)

				self.db_session.add(m)
				edgeinfo = EdgeLookup(m.ad_id, m.objectSid, 'group')
				self.db_session.add(edgeinfo)

				if self.bloodhound_version == '2':
					for item in groups['Members']:
						q_ad_name = groups['Name'].rsplit('@', 1)[1]
						q_ad_id = self.adn[q_ad_name]
						q_groupname = groups['Name'].split('@', 1)[0]
						res = self.db_session.query(Group).filter_by(name = q_groupname).filter(Group.ad_id == q_ad_id).first()
						if res is None:
							raise Exception('Group not found ! %s ' % groups['Name'])
						self.add_edge(res.objectSid, BHImport.member_type_lookup(item['MemberType']), m.oid, 'group', 'member', self.adn[ad_name])
					
				else:
					for item in groups['Members']:
						self.add_edge(item['MemberId'], BHImport.member_type_lookup(item['MemberType']), m.oid, 'group', 'member', self.adn[ad_name])
					
				if  groups['Aces'] is not None:
					self.insert_acl(m.oid, 'group', groups['Aces'], m.ad_id)
				
			except Exception as e:
				logger.debug('[BHIMPORT] Error while processing group %s Reason: %s' % (groups, e))
				continue

		self.db_session.commit()

	def get_file(self, filetype):
		if self.is_zip is True:
			with zipfile.ZipFile(self.filepath, 'r') as zf:
				with zf.open(self.fd[filetype]) as data:
					return json.load(data)

	@staticmethod
	def from_zipfile(filepath):
		bh = BHImport()
		bh.filepath = filepath
		if not zipfile.is_zipfile(filepath):
			raise Exception('The file on this path doesnt look like a valid zip file! %s' % filepath)
		
		bh.is_zip = True
		zip = zipfile.ZipFile(filepath, 'r')
		for filename in zip.namelist():
			if filename.find('_computers.json') != -1:
				bh.fd['computers'] = filename
			elif filename.find('_domains.json') != -1:
				bh.fd['domains'] = filename
			elif filename.find('_gpos.json') != -1:
				bh.fd['gpos'] = filename
			elif filename.find('_groups.json') != -1:
				bh.fd['groups'] = filename
			elif filename.find('_ous.json') != -1:
				bh.fd['ous'] = filename
			elif filename.find('_sessions.json') != -1:
				bh.fd['sessions'] = filename
			elif filename.find('_users.json') != -1:
				bh.fd['users'] = filename

		return bh

	def from_folder(self, folderpath):
		pass
	
	def set_debug(self, is_debug = True):
		self.debug = is_debug

	def test_paramsearch(self):
		pl = {}

		for groups in self.get_file('groups')['groups']:
			for ace in groups['Aces']:
				pl[ace['RightName']] = 1

		for gpo in self.get_file('gpos')['gpos']:
			for ace in gpo['Aces']:
				pl[ace['RightName']] = 1

		for domain in self.get_file('domains')['domains']:#['computers']:
			for ace in domain['Aces']:
				pl[ace['RightName']] = 1
		
		for ou in self.get_file('ous')['ous']:
			for ace in ou['Aces']:
				pl[ace['RightName']] = 1


		#for session in self.get_file('sessions')['sessions']:
		#	for ace in session['Aces']:
		#		for k in ace.keys():
		#			pl[k] = 1

		
		for user in self.get_file('users')['users']:
			for ace in user['Aces']:
				pl[ace['RightName']] = 1

		for machine in self.get_file('computers')['computers']:
			for ace in machine['Aces']:
				pl[ace['RightName']] = 1

		print(pl)

	def run(self):
		#DO NOT CHANGE THIS ORDER!!!!
		self.setup_db()

		self.import_domains()
		self.import_groups()
		self.import_users()
		self.import_machines()
		self.import_gpos()
		self.import_ous()
		
		if self.bloodhound_version == '2':
			self.import_sessions()
		
		self.insert_spns()
		self.insert_edges()
		self.insert_all_acls()
		self.db_session.commit()


if __name__ == '__main__':
	import sys
	db_conn = 'sqlite:///bhtest.db'
	filepath = sys.argv[1]

	logger.setLevel(1)
	create_db(db_conn)
	bh = BHImport.from_zipfile(filepath)
	bh.db_conn = db_conn
	bh.set_debug(False)
	bh.run()

