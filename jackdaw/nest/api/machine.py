
from flask import current_app
from jackdaw.dbmodel.aduser import JackDawADUser
from jackdaw.dbmodel.adcomp import JackDawADMachine
from jackdaw.dbmodel.adinfo import JackDawADInfo
from jackdaw.dbmodel.smbfinger import SMBFinger

def list_machines(domainid, page, maxcnt):
	db = current_app.db
	res = {
		'res' : [],
		'page': {},
	}
	qry = db.session.query(
		JackDawADMachine
		).filter_by(ad_id = domainid
		).with_entities(
			JackDawADMachine.id, 
			JackDawADMachine.objectSid, 
			JackDawADMachine.sAMAccountName
		)
	
	qry = qry.paginate(page = page, max_per_page = maxcnt)

	domains = []
	for uid, sid, name in qry.items:
		domains.append(
			{
				'id' : uid, 
				'sid' : sid, 
				'name': name
			}
		)

	page = dict(
		total=qry.total, 
		current_page=qry.page,
		per_page=qry.per_page
	)

	res['res'] = domains
	res['page'] = page

	return res

def get(domainid, machineid):
	db = current_app.db
	machine = db.session.query(JackDawADMachine).get(machineid)
	return machine.to_dict()

def get_sid(domainid, sid):
	db = current_app.db
	for machine in db.session.query(JackDawADMachine).filter_by(objectSid = sid).filter(JackDawADMachine.ad_id == domainid).all():
		return machine.to_dict()

def get_os_versions(domainid):
	db = current_app.db
	qry = db.session.query(
		JackDawADMachine.operatingSystemVersion
		).filter_by(ad_id = domainid
		).group_by(JackDawADMachine.operatingSystemVersion
		).distinct(JackDawADMachine.operatingSystemVersion)

	versions = {}
	for version in qry.all():
		versions[version[0]] = 1
	
	return list(versions.keys())

def get_domains(domainid):
	db = current_app.db
	qry = db.session.query(
			SMBFinger.domainname
			).filter(JackDawADMachine.ad_id == domainid
			).filter(JackDawADInfo.id == domainid
			).filter(SMBFinger.machine_id == JackDawADMachine.id
			).group_by(SMBFinger.domainname)

	domains = {}
	for domain in qry.all():
		domains[domain[0]] = 1
	
	return list(domains.keys())