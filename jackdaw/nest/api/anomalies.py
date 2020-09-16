from flask import current_app
from jackdaw.dbmodel.aduser import ADUser
from jackdaw.dbmodel.adcomp import Machine
from jackdaw.dbmodel.adinfo import ADInfo
from jackdaw.dbmodel.smbfinger import SMBFinger
from jackdaw.nest.anomalies.anomalies import Anomalies


def get_user_pwnotreq(domainid, page, maxcnt):
	anom = Anomalies(current_app, db_session = current_app.db)
	res = anom.get_user_pwnotreq(domainid, page, maxcnt)
	return res

def get_user_plaintext(domainid, page, maxcnt):
	anom = Anomalies(current_app, db_session = current_app.db)
	res = anom.get_user_plaintext(domainid, page, maxcnt)
	return res

def get_user_pw_notexp(domainid, page, maxcnt):
	anom = Anomalies(current_app, db_session = current_app.db)
	res = anom.get_user_pw_notexp(domainid, page, maxcnt)
	return res

def get_user_des_only(domainid, page, maxcnt):
	anom = Anomalies(current_app, db_session = current_app.db)
	res = anom.get_user_des_only(domainid, page, maxcnt)
	return res

def get_user_asrep(domainid, page, maxcnt):
	anom = Anomalies(current_app, db_session = current_app.db)
	res = anom.get_user_asrep(domainid, page, maxcnt)
	return res

def get_user_description(domainid, page, maxcnt):
	anom = Anomalies(current_app, db_session = current_app.db)
	res = anom.get_user_description(domainid, page, maxcnt)
	return res

def get_machine_description(domainid, page, maxcnt):
	anom = Anomalies(current_app, db_session = current_app.db)
	res = anom.get_machine_description(domainid, page, maxcnt)
	return res

def get_machine_outdated(domainid, version, page, maxcnt):
	anom = Anomalies(current_app, db_session = current_app.db)
	res = anom.get_machine_outdated(domainid, version, page, maxcnt)
	return res

def get_smb_nosig(domainid, page, maxcnt):
	anom = Anomalies(current_app, db_session = current_app.db)
	res = anom.get_smb_nosig(domainid, page, maxcnt)
	return res

def get_smb_domain_mismatch(domainid, page, maxcnt):
	anom = Anomalies(current_app, db_session = current_app.db)
	res = anom.get_smb_domain_mismatch(domainid, page, maxcnt)
	return res

def get_statistics(domainid, graphid = None):
	anom = Anomalies(current_app, db_session = current_app.db)
	res = anom.get_statistics(domainid, graphid)
	return res
	