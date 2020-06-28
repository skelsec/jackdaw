from flask import current_app
from jackdaw.dbmodel.aduser import ADUser
from jackdaw.dbmodel.adcomp import Machine
from jackdaw.dbmodel.adinfo import ADInfo
from jackdaw.dbmodel.smbfinger import SMBFinger
import base64


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
			Machine.id, Machine.sAMAccountName, SMBFinger.objectSid
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




