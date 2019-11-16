from flask import current_app
from jackdaw.dbmodel.aduser import JackDawADUser
from jackdaw.dbmodel.adcomp import JackDawADMachine
from jackdaw.dbmodel.adinfo import JackDawADInfo
from jackdaw.dbmodel.smbfinger import SMBFinger

def get_user_uac_problems(domainid):
	db = current_app.db
	pw_notreq_users = []
	for uid, username in db.session.query(JackDawADUser).filter_by(ad_id = domainid).filter(JackDawADUser.UAC_PASSWD_NOTREQD == True).with_entities(JackDawADUser.id, JackDawADUser.sAMAccountName).all():
		pw_notreq_users.append([uid, username])

	plaintext_pw_users = []
	for uid, username in db.session.query(JackDawADUser).filter_by(ad_id = domainid).filter(JackDawADUser.UAC_ENCRYPTED_TEXT_PASSWORD_ALLOWED == True).with_entities(JackDawADUser.id, JackDawADUser.sAMAccountName).all():
		plaintext_pw_users.append([uid, username])

	pw_notexp = []
	for uid, username in db.session.query(JackDawADUser).filter_by(ad_id = domainid).filter(JackDawADUser.UAC_DONT_EXPIRE_PASSWD == True).with_entities(JackDawADUser.id, JackDawADUser.sAMAccountName).all():
		pw_notexp.append([uid, username])

	des_only = []
	for uid, username in db.session.query(JackDawADUser).filter_by(ad_id = domainid).filter(JackDawADUser.UAC_USE_DES_KEY_ONLY == True).with_entities(JackDawADUser.id, JackDawADUser.sAMAccountName).all():
		des_only.append([uid, username])  

	asrep = []
	for uid, username in db.session.query(JackDawADUser).filter_by(ad_id = domainid).filter(JackDawADUser.UAC_DONT_REQUIRE_PREAUTH == True).with_entities(JackDawADUser.id, JackDawADUser.sAMAccountName).all():
		asrep.append([uid, username])
	
	return {
		'pw_notreq_users':  pw_notreq_users,
		'plaintext_pw_users':  plaintext_pw_users,
		'pw_notexp':  pw_notexp,
		'des_only':  des_only,
		'asrep':  asrep,
	}

def get_outdated_os(domainid):
	#TODO: implement filtering!!!
	db = current_app.db
	outdated_hosts = {} #version - samaccountname,id
	versions = {}
	for x in db.session.query(JackDawADMachine.operatingSystemVersion).filter_by(ad_id = domainid).group_by(JackDawADMachine.operatingSystemVersion).distinct():
		versions[x[0]] = 1

	#TODO: do filtering here!
	filtered_versions = versions
	for version in filtered_versions:
		#version = None if version == '' else version
		for mid, name in db.session.query(JackDawADMachine.operatingSystemVersion).filter_by(ad_id = domainid).filter(JackDawADMachine.operatingSystemVersion == version).with_entities(JackDawADMachine.id, JackDawADMachine.sAMAccountName).all():
			if version not in outdated_hosts:
				outdated_hosts[version] = []
			outdated_hosts[version].append([mid, name])
	
	return outdated_hosts

def get_smb_nosig(domainid):
	db = current_app.db
	machines = []
	for mid, name, _ in db.session.query(JackDawADMachine.id, JackDawADMachine.sAMAccountName , SMBFinger.id
								).filter(JackDawADMachine.ad_id == domainid
								).filter(SMBFinger.machine_id == JackDawADMachine.id
								).filter(SMBFinger.signing_required == False
								).all():
		machines.append({
				'id' : mid,
				'name' : name,
			})
	
	return machines

def get_smb_domain_mismatch(domainid):
	db = current_app.db
	machines = []
	for _, mid, name, domain in db.session.query(JackDawADInfo.id, JackDawADMachine.id, JackDawADMachine.sAMAccountName , SMBFinger.domainname
								).filter(JackDawADMachine.ad_id == domainid
								).filter(JackDawADInfo.id == domainid
								).filter(SMBFinger.machine_id == JackDawADMachine.id
								).filter(SMBFinger.domainname != JackDawADInfo.name
								).filter(SMBFinger.domainname != None
								).all():
		machines.append({
				'machineid' : mid,
				'machinename' : name,
				'domainname' : domain,
			})
	
	return machines

def get_machine_description(domainid):
	db = current_app.db
	machines = []
	for mid, name, description in db.session.query(JackDawADMachine.id, JackDawADMachine.sAMAccountName, JackDawADMachine.description
								).filter(JackDawADMachine.ad_id == domainid
								).filter(JackDawADMachine.description != None
								).filter(JackDawADMachine.description != ""
								).all():
		machines.append({
				'machineid' : mid,
				'machinename' : name,
				'description' : description,
			})
	
	return machines

def get_user_description(domainid):
	db = current_app.db
	users = []
	for mid, name, description in db.session.query(JackDawADUser.id, JackDawADUser.sAMAccountName, JackDawADUser.description
								).filter(JackDawADUser.ad_id == domainid
								).filter(JackDawADUser.description != None
								).filter(JackDawADUser.description != ""
								).all():
		users.append({
				'userid' : mid,
				'username' : name,
				'description' : description,
			})
	
	return users