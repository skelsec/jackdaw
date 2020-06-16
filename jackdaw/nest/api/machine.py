
from flask import current_app
from jackdaw.dbmodel.aduser import ADUser
from jackdaw.dbmodel.adcomp import Machine
from jackdaw.dbmodel.adinfo import ADInfo
from jackdaw.dbmodel.smbfinger import SMBFinger

def list_machines(domainid, page, maxcnt):
	db = current_app.db
	res = {
		'res' : [],
		'page': {},
	}
	qry = db.session.query(
		Machine
		).filter_by(ad_id = domainid
		).with_entities(
			Machine.id, 
			Machine.objectSid, 
			Machine.sAMAccountName
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
	machine = db.session.query(Machine).get(machineid)
	return machine.to_dict()

def get_sid(domainid, sid):
	db = current_app.db
	for machine in db.session.query(Machine).filter_by(objectSid = sid).filter(Machine.ad_id == domainid).all():
		return machine.to_dict()

def get_os_versions(domainid):
	db = current_app.db
	qry = db.session.query(
		Machine.operatingSystemVersion
		).filter_by(ad_id = domainid
		).group_by(Machine.operatingSystemVersion
		).distinct(Machine.operatingSystemVersion)

	versions = {}
	for version in qry.all():
		versions[version[0]] = 1
	
	return list(versions.keys())

def get_domains(domainid):
	db = current_app.db
	qry = db.session.query(
			SMBFinger.domainname
			).filter(Machine.ad_id == domainid
			).filter(ADInfo.id == domainid
			).filter(SMBFinger.machine_id == Machine.id
			).group_by(SMBFinger.domainname)

	domains = {}
	for domain in qry.all():
		domains[domain[0]] = 1
	
	return list(domains.keys())