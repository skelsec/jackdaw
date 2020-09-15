from flask import current_app
from jackdaw.dbmodel.aduser import ADUser
from jackdaw.dbmodel.adcomp import Machine
from jackdaw.dbmodel.adinfo import ADInfo
from jackdaw.dbmodel.smbfinger import SMBFinger
from jackdaw.dbmodel.netshare import NetShare
import base64
import string
import datetime


class Anomalies:
	def __init__(self, db_conn = None, db_session = None):
		self.db_conn = db_conn
		self.db_session = db_session


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

	def get_statistics(self, domainid):
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
			).filter(ADUser.canLogon == True)

		plaintext_pw_users_qry = self.db_session.session.query(
			ADUser.id
			).filter_by(ad_id = domainid
			).filter(ADUser.UAC_ENCRYPTED_TEXT_PASSWORD_ALLOWED == True
			).filter(ADUser.canLogon == True)

		plaintext_pw_dontexpire_qry = self.db_session.session.query(
			ADUser.id
			).filter_by(ad_id = domainid
			).filter(ADUser.UAC_DONT_EXPIRE_PASSWD == True
			).filter(ADUser.canLogon == True)

		nopreauth_qry = self.db_session.session.query(
			ADUser.id
			).filter_by(ad_id = domainid
			).filter(ADUser.UAC_DONT_REQUIRE_PREAUTH == True
			).filter(ADUser.canLogon == True)
		
		extremely_old_passwords_qry = self.db_session.session.query(
			ADUser.id
			).filter_by(ad_id = domainid
			).filter(ADUser.pwdLastSet < (datetime.datetime.utcnow() - datetime.timedelta(weeks=52))
			).filter(ADUser.canLogon == True)

		user_pw_never_changed_qry = self.db_session.session.query(
			ADUser.id
			).filter_by(ad_id = domainid
			).filter(ADUser.pwdLastSet == ADUser.whenCreated
			).filter(ADUser.canLogon == True)

		smb_singing_noteq_qry = self.db_session.session.query(
			Machine.id, Machine.sAMAccountName, SMBFinger.machine_sid
			).filter(Machine.ad_id == domainid
			).filter(SMBFinger.machine_sid == Machine.objectSid
			).filter(SMBFinger.signing_required == False
			)

		default_shares = ['print$','IPC$','ADMIN$', 'SYSVOL', 'NETLOGON']
		for x in string.ascii_uppercase:
			default_shares.append('%s$' % x)

		smb_nondefault_shares_qry = self.db_session.session.query(
			NetShare.id
			).filter_by(ad_id = domainid
			).distinct(NetShare.netname
			).filter(NetShare.netname.notin_(default_shares)
			)


		users_total_count = total_users_qry.count()
		users_active_count = users_active_qry.count()
		machines_total_count = total_machines_qry.count()
		

		user_pw_notreq_count = pw_notreq_qry.count()
		user_pw_plaintext_count = plaintext_pw_users_qry.count()
		user_pw_dontexpire_count = plaintext_pw_dontexpire_qry.count()
		user_pw_nopreauth_count = nopreauth_qry.count()
		user_extremely_old_passwords_count = extremely_old_passwords_qry.count()
		user_pw_never_changed_count = user_pw_never_changed_qry.count()
		

		machine_smb_nosig_count = smb_singing_noteq_qry.count()
		machine_smb_non_standard_shares_count = smb_nondefault_shares_qry.count()
		machnie_outdated_os_count = 1

		return {
			'users_total_count' : users_total_count,
			'users_active_count': users_active_count,
			'machines_total_count' : machines_total_count,
			'user_pw_notreq_count' : user_pw_notreq_count,
			'user_pw_plaintext_count' : user_pw_plaintext_count,
			'user_pw_dontexpire_count' : user_pw_dontexpire_count,
			'user_pw_nopreauth_count' : user_pw_nopreauth_count,
			'user_extremely_old_passwords_count' : user_extremely_old_passwords_count,
			'user_pw_never_changed_count' : user_pw_never_changed_count,

			'machine_smb_nosig_count' : machine_smb_nosig_count,
			'machine_smb_non_standard_shares_count' : machine_smb_non_standard_shares_count,
			'machnie_outdated_os_count' : machnie_outdated_os_count,
		}

