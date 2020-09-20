from flask import current_app
from jackdaw.dbmodel.aduser import ADUser
from jackdaw.dbmodel.adcomp import Machine
from jackdaw.dbmodel.adinfo import ADInfo
from jackdaw.dbmodel.adgroup import Group
from jackdaw.dbmodel.smbfinger import SMBFinger
from jackdaw.dbmodel.netshare import NetShare
from jackdaw.dbmodel.smbprotocols import SMBProtocols
from jackdaw.nest.graph.graphdata import GraphData

import base64
import string
import datetime

class Issue:
	def __init__(self, severity, name, description, confidence, recommendation = None, category = None):
		self.severity = severity
		self.confidence = confidence
		self.name = name
		self.description = description
		self.recommendation = recommendation
		self.affected_ids = []
		self.category = category

	def to_dict(self):
		return {
			'severity' : self.severity,
			'confidence' : self.confidence,
			'name' : self.name,
			'description' : self.description,
			'recommendation' : 'lorem ipsum stuf.... http://microsoft.com/', #this is for debug only, fix this!
			'affected_ids' : self.affected_ids,
			'category' : self.category,	
		}

class Anomalies:
	def __init__(self, current_app, db_conn = None, db_session = None):
		self.db_conn = db_conn
		self.db_session = db_session
		self.current_app = current_app


	def get_user_pwnotreq(self, domainid, page, maxcnt):
		res = {
			'res' : [],
			'page': {},
		}
		pw_notreq_users = []

		qry = self.db_session.session.query(
			ADUser
			).filter_by(ad_id = domainid
			).filter(ADUser.UAC_PASSWD_NOTREQD == True
			).with_entities(ADUser.id, ADUser.sAMAccountName
			)
			
		qry = qry.paginate(page = page, max_per_page = maxcnt)
		for uid, username in qry.items:
			pw_notreq_users.append(
				{
					'uid' : uid, 
					'username' : username
				}
			)
		page = dict(
			total=qry.total, 
			current_page=qry.page,
			per_page=qry.per_page
		)

		res['res'] = pw_notreq_users
		res['page'] = page

		return res

	def get_user_plaintext(self, domainid, page, maxcnt):
		res = {
			'res' : [],
			'page': {},
		}
		plaintext_pw_users = []
		qry = self.db_session.session.query(
			ADUser
			).filter_by(ad_id = domainid
			).filter(ADUser.UAC_ENCRYPTED_TEXT_PASSWORD_ALLOWED == True
			).with_entities(ADUser.id, ADUser.sAMAccountName
			)

		qry = qry.paginate(page = page, max_per_page = maxcnt)
		
		for uid, username in qry.items:
			plaintext_pw_users.append(
				{
					'uid' : uid, 
					'username' : username
				}
			)

		page = dict(
			total=qry.total, 
			current_page=qry.page,
			per_page=qry.per_page
		)

		res['res'] = plaintext_pw_users
		res['page'] = page

		return res

	def get_user_pw_notexp(self, domainid, page, maxcnt):
		res = {
			'res' : [],
			'page': {},
		}
		pw_notexp = []
		qry = self.db_session.session.query(
			ADUser
			).filter_by(ad_id = domainid
			).filter(ADUser.UAC_DONT_EXPIRE_PASSWD == True
			).with_entities(ADUser.id, ADUser.sAMAccountName
			)

		qry = qry.paginate(page = page, max_per_page = maxcnt)
		for uid, username in qry.items:
			pw_notexp.append(
				{
					'uid' : uid, 
					'username' : username
				}
			)

		page = dict(
			total=qry.total, 
			current_page=qry.page,
			per_page=qry.per_page
		)

		res['res'] = pw_notexp
		res['page'] = page

		return res

	def get_user_des_only(self, domainid, page, maxcnt):
		res = {
			'res' : [],
			'page': {},
		}
		des_only = []
		qry = self.db_session.session.query(
			ADUser
			).filter_by(ad_id = domainid
			).filter(ADUser.UAC_USE_DES_KEY_ONLY == True
			).with_entities(ADUser.id, ADUser.sAMAccountName
			)

		qry = qry.paginate(page = page, max_per_page = maxcnt)
		for uid, username in qry.items:
			des_only.append(
				{
					'uid' : uid, 
					'username' : username
				}
			)

		page = dict(
			total=qry.total, 
			current_page=qry.page,
			per_page=qry.per_page
		)

		res['res'] = des_only
		res['page'] = page

		return res

	def get_user_asrep(self, domainid, page, maxcnt):
		res = {
			'res' : [],
			'page': {},
		}
		asrep = []
		qry = self.db_session.session.query(
			ADUser
			).filter_by(ad_id = domainid
			).filter(ADUser.UAC_DONT_REQUIRE_PREAUTH == True
			).with_entities(ADUser.id, ADUser.sAMAccountName
			)

		qry = qry.paginate(page = page, max_per_page = maxcnt)
		for uid, username in qry.items:
			asrep.append(
				{
					'uid' : uid, 
					'username' : username
				}
			)

		page = dict(
			total=qry.total, 
			current_page=qry.page,
			per_page=qry.per_page
		)

		res['res'] = asrep
		res['page'] = page

		return res

		
	def get_user_description(self, domainid, page, maxcnt):
		res = {
			'res' : [],
			'page': {},
		}
		users = []
		qry = self.db_session.session.query(
			ADUser.id, ADUser.sAMAccountName, ADUser.description
			).filter(ADUser.ad_id == domainid
			).filter(ADUser.description != None
			).filter(ADUser.description != ""
			)

		qry = qry.paginate(page = page, max_per_page = maxcnt)
		for mid, name, description in qry.items:
			users.append({
					'userid' : mid,
					'username' : name,
					'description' : description,
				})
		
		page = dict(
			total=qry.total, 
			current_page=qry.page,
			per_page=qry.per_page
		)

		res['res'] = users
		res['page'] = page

		return res

	def get_machine_description(self, domainid, page, maxcnt):
		res = {
			'res' : [],
			'page': {},
		}
		machines = []
		qry = self.db_session.session.query(
			Machine.id, Machine.sAMAccountName, Machine.description
			).filter(Machine.ad_id == domainid
			).filter(Machine.description != None
			).filter(Machine.description != ""
			)

		qry = qry.paginate(page = page, max_per_page = maxcnt)
		for mid, name, description in qry.items:
			machines.append({
					'machineid' : mid,
					'machinename' : name,
					'description' : description,
				})
		
		page = dict(
			total=qry.total, 
			current_page=qry.page,
			per_page=qry.per_page
		)

		res['res'] = machines
		res['page'] = page

		return res

	def get_machine_outdated(self, domainid, version, page, maxcnt):
		res = {
			'res' : [],
			'page': {},
		}
		version = base64.b64decode(version).decode()
		# TODO: input filtering more? not sure if needed here...
		machines = []
		qry = self.db_session.session.query(
			Machine
			).filter_by(ad_id = domainid
			).filter(Machine.operatingSystemVersion == version
			).with_entities(Machine.id, Machine.sAMAccountName, Machine.objectSid
			)
		
		qry = qry.paginate(page = page, max_per_page = maxcnt)
		for mid, name, sid in qry.items:
			machines.append({
					'machineid' : mid,
					'machinename' : name,
					'machinesid' : sid
				})
		
		page = dict(
			total=qry.total, 
			current_page=qry.page,
			per_page=qry.per_page
		)

		res['res'] = machines
		res['page'] = page

		return res


	def get_smb_nosig(self, domainid, page, maxcnt):
		res = {
			'res' : [],
			'page': {},
		}
		machines = []
		qry = self.db_session.session.query(
			Machine.id, Machine.sAMAccountName, SMBFinger.machine_sid
			).filter(Machine.ad_id == domainid
			).filter(SMBFinger.machine_sid == Machine.objectSid
			).filter(SMBFinger.signing_required == False
			)

		qry = qry.paginate(page = page, max_per_page = maxcnt)
		for mid, name, _ in qry.items:
			machines.append({
					'id' : mid,
					'name' : name,
				})
		
		page = dict(
			total=qry.total, 
			current_page=qry.page,
			per_page=qry.per_page
		)

		res['res'] = machines
		res['page'] = page

		return res


	def get_smb_domain_mismatch(self, domainid, page, maxcnt):
		res = {
			'res' : [],
			'page': {},
		}
		machines = []
		qry = self.db_session.session.query(
			ADInfo.id, Machine.id, Machine.sAMAccountName , SMBFinger.domainname
			).filter(Machine.ad_id == domainid
			).filter(ADInfo.id == domainid
			).filter(SMBFinger.machine_sid == Machine.objectSid
			).filter(SMBFinger.domainname != ADInfo.name
			).filter(SMBFinger.domainname != None
			)

		qry = qry.paginate(page = page, max_per_page = maxcnt)
		for _, mid, name, domain in qry.items:
			machines.append({
					'machineid' : mid,
					'machinename' : name,
					'domainname' : domain,
				})
		
		page = dict(
			total=qry.total, 
			current_page=qry.page,
			per_page=qry.per_page
		)

		res['res'] = machines
		res['page'] = page

		return res

	def __graph_distance_da(self, domainid, graphid):
		da_sids = {}
		for res in self.current_app.db.session.query(Group).filter_by(ad_id = self.current_app.config['JACKDAW_GRAPH_DICT'][graphid].domain_id).filter(Group.objectSid.like('%-512')).all():
			da_sids[res.objectSid] = 0
			
		if len(da_sids) == 0:
			raise Exception('No domain admins found!')
			
		res = GraphData()
		for sid in da_sids:
			res += current_app.config['JACKDAW_GRAPH_DICT'][graphid].shortest_paths(None, sid)

		distances = {}
		for node in res.nodes:
			if res.nodes[node].mindistance not in distances:
				distances[res.nodes[node].mindistance] = 0
			distances[res.nodes[node].mindistance] += 1
			#print('%s (%s)' % (res.nodes[node].name, res.nodes[node].mindistance))
		
		return distances

	def __graph_kerberoast_to_da(self, domainid, graphid):
		target_sids = {}
		da_sids = {}

		for res in self.current_app.db.session.query(Group).filter_by(ad_id = self.current_app.config['JACKDAW_GRAPH_DICT'][graphid].domain_id).filter(Group.objectSid.like('%-512')).all():
			da_sids[res.objectSid] = 0

		for res in self.current_app.db.session.query(ADUser.objectSid)\
			.filter_by(ad_id = self.current_app.config['JACKDAW_GRAPH_DICT'][graphid].domain_id)\
			.filter(ADUser.servicePrincipalName != None).all():
				
			target_sids[res[0]] = 0

		res = GraphData()
		for dst_sid in da_sids:
			for src_sid in target_sids:
				res += self.current_app.config['JACKDAW_GRAPH_DICT'][graphid].shortest_paths(src_sid, dst_sid)

		kerb_count = 0
		for node in res.nodes:
			if node in target_sids:
				kerb_count += 1
				del target_sids[node] #disposing the found ndoe, to avoid dupes
			
		return kerb_count

	def __graph_asreproast_to_da(self, domainid, graphid):
		target_sids = {}
		da_sids = {}

		for res in self.current_app.db.session.query(Group).filter_by(ad_id = self.current_app.config['JACKDAW_GRAPH_DICT'][graphid].domain_id).filter(Group.objectSid.like('%-512')).all():
			da_sids[res.objectSid] = 0

		for res in self.current_app.db.session.query(ADUser.objectSid)\
			.filter_by(ad_id = self.current_app.config['JACKDAW_GRAPH_DICT'][graphid].domain_id)\
			.filter(ADUser.UAC_DONT_REQUIRE_PREAUTH == True).all():
			
			target_sids[res[0]] = 0

		res = GraphData()
		for dst_sid in da_sids:
			for src_sid in target_sids:
				res += self.current_app.config['JACKDAW_GRAPH_DICT'][graphid].shortest_paths(src_sid, dst_sid)
			
		kerb_count = 0
		for node in res.nodes:
			if node in target_sids:
				kerb_count += 1
				del target_sids[node] #disposing the found ndoe, to avoid dupes
			
		return kerb_count

	def eval_stats(self, stat_dict, domainid):
		
		issues = []
		
		if stat_dict['user_pw_notreq_active_count'] > 0:
			p = Issue('LOW', 'Users with password not required flag set', 'Usually this is not a problem, just someting installers forget to change', 100)
			for sid in self.db_session.session.query(ADUser.id).filter_by(ad_id = domainid).filter(ADUser.UAC_PASSWD_NOTREQD == True).all():
				p.affected_ids.append((sid[0], 'user'))
			issues.append(p)

		if stat_dict['user_pw_plaintext_active_count'] > 0:
			p = Issue('MEDIUM', 'User password stored on the domain controller in plaintext format', '', 100)
			for sid in self.db_session.session.query(ADUser.id).filter_by(ad_id = domainid).filter(ADUser.UAC_ENCRYPTED_TEXT_PASSWORD_ALLOWED == True).all():
				p.affected_ids.append((sid[0], 'user'))
			issues.append(p)

		if stat_dict['user_pw_dontexpire_active_count'] > 0:
			p = Issue('MEDIUM', 'User password never expires', '', 100)
			for sid in self.db_session.session.query(ADUser.id).filter_by(ad_id = domainid).filter(ADUser.UAC_DONT_EXPIRE_PASSWD == True).all():
				p.affected_ids.append((sid[0], 'user'))
			issues.append(p)

		if stat_dict['user_pw_nopreauth_active_count'] > 0:
			p = Issue('MEDIUM', 'User prone to ASREP roast attack', '', 100)
			for sid in self.db_session.session.query(ADUser.id).filter_by(ad_id = domainid).filter(ADUser.UAC_DONT_REQUIRE_PREAUTH == True).all():
				p.affected_ids.append((sid[0], 'user'))
			issues.append(p)

		if stat_dict['user_extremely_old_passwords_active_count'] > 0:
			p = Issue('HIGH', 'User password has not changed since a year', '', 100)
			for sid in self.db_session.session.query(ADUser.id).filter_by(ad_id = domainid).filter(ADUser.pwdLastSet < (datetime.datetime.utcnow() - datetime.timedelta(weeks=52))).all():
				p.affected_ids.append((sid[0], 'user'))
			issues.append(p)

		if stat_dict['user_pw_never_changed_active_count'] > 0:
			p = Issue('HIGH', 'User password has not changed since its creation', '', 100)
			for sid in self.db_session.session.query(ADUser.id).filter_by(ad_id = domainid).filter(ADUser.pwdLastSet == ADUser.whenCreated).all():
				p.affected_ids.append((sid[0], 'user'))
			issues.append(p)

		if stat_dict['user_kerberoastable_active_count'] > 0:
			p = Issue('MEDIUM', 'User is prone to kerberoast attack', 'attack sucsess rate depends on the strength of the user\'s password', 100)
			for sid in self.db_session.session.query(ADUser.id).filter_by(ad_id = domainid).filter(ADUser.servicePrincipalName != None).all():
				p.affected_ids.append((sid[0], 'user'))
			issues.append(p)

		if stat_dict['machine_smb_nosig_count'] > 0:
			p = Issue('MEDIUM', 'Machine doesn\'t enforce NTLm signing', '', 100)
			for sid in self.db_session.session.query(Machine.id, Machine.sAMAccountName, SMBFinger.machine_sid).filter(Machine.ad_id == domainid).filter(SMBFinger.machine_sid == Machine.objectSid).filter(SMBFinger.signing_required == False).all():
				p.affected_ids.append((sid[0], 'machine'))
			issues.append(p)

		if stat_dict['machine_smb_non_standard_shares_count'] > 0:
			p = Issue('LOW', 'Machine has shares', '', 100)
			issues.append(p)

		if stat_dict['machnie_outdated_os_count'] > 0:
			p = Issue('HIGH', 'Machine OS is outdated', '', 100)
			issues.append(p)

		if stat_dict['machine_smb_smb1_dialect_count'] > 0:
			p = Issue('HIGH', 'Machine supports SMBv1, this is terrible', '', 100)
			for sid in self.db_session.session.query(SMBProtocols.machine_sid,).filter(SMBProtocols.ad_id == domainid).filter(SMBProtocols.protocol == 'SMB1').distinct(SMBProtocols.machine_sid).all():
				p.affected_ids.append(sid[0])
			issues.append(p)

		if 'graph_distances_to_da' in stat_dict:
			user_cnt = 0
			for distance in stat_dict['graph_distances_to_da']:
				if distance < 3:
					user_cnt += stat_dict['graph_distances_to_da'][distance]
			
			if user_cnt > stat_dict['users_active_count'] // 10:
				p = Issue('HIGH', 'Unusually large set of users close to domain administrators', '', 100)
				issues.append(p)


		if 'graph_count_kerberoast_to_da' in stat_dict:
			if stat_dict['graph_count_kerberoast_to_da'] > 0:
				p = Issue('HIGH', 'User with Kerberoast vulnerability has potential domain administrator access', '', 100)
				issues.append(p)
		
		if 'graph_count_asreproast_to_da' in stat_dict:
			if stat_dict['graph_count_asreproast_to_da'] > 0:
				p = Issue('HIGH', 'User with ASREP roast vulnerability has potential domain administrator access', '', 100)
				issues.append(p)

		score = self.eval_issues(issues)
		return [x.to_dict() for x in issues], score

	def eval_issues(self, issues):
		#this is a placeholder, ovbiously need a scoring system implemented here
		# TODO
		res = 0
		for issue in issues:
			if issue.severity == 'HIGH':
				res += 10
			
			elif issue.severity == 'MEDIUM':
				res += 5

			elif issue.severity == 'LOW':
				res += 2

		return res

	def get_statistics(self, domainid, graphid = None):
		# not pageable
		
		total_users_qry = self.db_session.session.query(
			ADUser.id
			).filter_by(ad_id = domainid
			)
		
		users_active_qry = self.db_session.session.query(
			ADUser.id
			).filter_by(ad_id = domainid
			).filter(ADUser.canLogon == True)
		
		total_machines_qry = self.db_session.session.query(
			Machine.id
			).filter_by(ad_id = domainid
			)
		
		pw_notreq_qry = self.db_session.session.query(
			ADUser.id
			).filter_by(ad_id = domainid
			).filter(ADUser.UAC_PASSWD_NOTREQD == True
			)

		plaintext_pw_users_qry = self.db_session.session.query(
			ADUser.id
			).filter_by(ad_id = domainid
			).filter(ADUser.UAC_ENCRYPTED_TEXT_PASSWORD_ALLOWED == True
			)

		plaintext_pw_dontexpire_qry = self.db_session.session.query(
			ADUser.id
			).filter_by(ad_id = domainid
			).filter(ADUser.UAC_DONT_EXPIRE_PASSWD == True
			)

		nopreauth_qry = self.db_session.session.query(
			ADUser.id
			).filter_by(ad_id = domainid
			).filter(ADUser.UAC_DONT_REQUIRE_PREAUTH == True
			)
		
		extremely_old_passwords_qry = self.db_session.session.query(
			ADUser.id
			).filter_by(ad_id = domainid
			).filter(ADUser.pwdLastSet < (datetime.datetime.utcnow() - datetime.timedelta(weeks=52))
			)

		user_pw_never_changed_qry = self.db_session.session.query(
			ADUser.id
			).filter_by(ad_id = domainid
			).filter(ADUser.pwdLastSet == ADUser.whenCreated
			)

		user_kerberoastable_qry = self.db_session.session.query(
			ADUser.id
			).filter_by(ad_id = domainid
			).filter(ADUser.servicePrincipalName != None
			)

		smb_singing_noteq_qry = self.db_session.session.query(
			Machine.id, Machine.sAMAccountName, SMBFinger.machine_sid
			).filter(Machine.ad_id == domainid
			).filter(SMBFinger.machine_sid == Machine.objectSid
			).filter(SMBFinger.signing_required == False
			)

		smb_smb1_dialect_qry = self.db_session.session.query(
			SMBProtocols.machine_sid
			).filter(SMBProtocols.ad_id == domainid
			).filter(SMBProtocols.protocol == 'SMB1'
			).distinct(SMBProtocols.machine_sid
			)

		default_shares = ['print$','IPC$','ADMIN$', 'SYSVOL', 'NETLOGON']
		for x in string.ascii_uppercase:
			default_shares.append('%s$' % x)

		smb_nondefault_shares_qry = self.db_session.session.query(
			NetShare.machine_sid
			).filter_by(ad_id = domainid
			).distinct(NetShare.machine_sid
			).filter(NetShare.netname.notin_(default_shares)
			)


		users_total_count = total_users_qry.count()
		users_active_count = users_active_qry.count()
		machines_total_count = total_machines_qry.count()
		

		user_pw_notreq_active_count = pw_notreq_qry.filter(ADUser.canLogon == True).count()
		user_pw_plaintext_active_count = plaintext_pw_users_qry.filter(ADUser.canLogon == True).count()
		user_pw_dontexpire_active_count = plaintext_pw_dontexpire_qry.filter(ADUser.canLogon == True).count()
		user_pw_nopreauth_active_count = nopreauth_qry.filter(ADUser.canLogon == True).count()
		user_extremely_old_passwords_active_count = extremely_old_passwords_qry.filter(ADUser.canLogon == True).count()
		user_pw_never_changed_active_count = user_pw_never_changed_qry.filter(ADUser.canLogon == True).count()
		user_kerberoastable_active_count = user_kerberoastable_qry.filter(ADUser.canLogon == True).count()

		user_pw_notreq_count = pw_notreq_qry.count()
		user_pw_plaintext_count = plaintext_pw_users_qry.count()
		user_pw_dontexpire_count = plaintext_pw_dontexpire_qry.count()
		user_pw_nopreauth_count = nopreauth_qry.count()
		user_extremely_old_passwords_count = extremely_old_passwords_qry.count()
		user_pw_never_changed_count = user_pw_never_changed_qry.count()
		user_kerberoastable_count = user_kerberoastable_qry.count()
		

		machine_smb_nosig_count = smb_singing_noteq_qry.count()
		machine_smb_non_standard_shares_count = smb_nondefault_shares_qry.count()
		machine_smb_smb1_dialect_count = smb_smb1_dialect_qry.count()

		#TODO: implement this
		machnie_outdated_os_count = 1
		machines_active_count = machines_total_count

		stat_dict = {
			'users_total_count' : users_total_count,
			'users_active_count': users_active_count,
			'machines_total_count' : machines_total_count,
			'machines_active_count' : machines_active_count,

			'user_pw_notreq_active_count' : user_pw_notreq_active_count,
			'user_pw_plaintext_active_count' : user_pw_plaintext_active_count,
			'user_pw_dontexpire_active_count' : user_pw_dontexpire_active_count,
			'user_pw_nopreauth_active_count' : user_pw_nopreauth_active_count,
			'user_extremely_old_passwords_active_count' : user_extremely_old_passwords_active_count,
			'user_pw_never_changed_active_count' : user_pw_never_changed_active_count,
			'user_kerberoastable_active_count' : user_kerberoastable_active_count,


			'user_pw_notreq_count' : user_pw_notreq_count,
			'user_pw_plaintext_count' : user_pw_plaintext_count,
			'user_pw_dontexpire_count' : user_pw_dontexpire_count,
			'user_pw_nopreauth_count' : user_pw_nopreauth_count,
			'user_extremely_old_passwords_count' : user_extremely_old_passwords_count,
			'user_pw_never_changed_count' : user_pw_never_changed_count,
			'user_kerberoastable_count' : user_kerberoastable_count,

			'machine_smb_nosig_count' : machine_smb_nosig_count,
			'machine_smb_non_standard_shares_count' : machine_smb_non_standard_shares_count,
			'machnie_outdated_os_count' : machnie_outdated_os_count,
			'machine_smb_smb1_dialect_count' : machine_smb_smb1_dialect_count,
		}


		if graphid is not None:
			if graphid not in self.current_app.config['JACKDAW_GRAPH_DICT']:
				graph_cache_dir = self.current_app.config['JACKDAW_WORK_DIR'].joinpath('graphcache')
				graph_dir = graph_cache_dir.joinpath(str(graphid))
				if graph_dir.exists() is False:
					raise Exception('Graph cache dir doesnt exists!')
				else:
					self.current_app.config['JACKDAW_GRAPH_DICT'][graphid] = self.current_app.config.get('JACKDAW_GRAPH_BACKEND_OBJ').load(current_app.db.session, graphid, graph_dir)
			
			

			stat_dict['graph_distances_to_da'] = self.__graph_distance_da(domainid, graphid)
			stat_dict['graph_count_kerberoast_to_da'] = self.__graph_kerberoast_to_da(domainid, graphid)
			stat_dict['graph_count_asreproast_to_da'] = self.__graph_asreproast_to_da(domainid, graphid)

		stat_dict['issues'], stat_dict['vuln_score']  = self.eval_stats(stat_dict, domainid)
		return stat_dict

