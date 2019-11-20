from flask import current_app
from jackdaw.dbmodel.adou import JackDawADOU

def list_ous(domainid, page, maxcnt):
	db = current_app.db
	res = {
		'res' : [],
		'page': {},
	}
	qry = db.session.query(
		JackDawADOU
		).filter_by(ad_id = domainid
		).with_entities(
			JackDawADOU.id, 
			JackDawADOU.objectGUID, 
			JackDawADOU.ou
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

def get(domainid, ouid):
	db = current_app.db
	user = db.session.query(JackDawADOU).get(ouid)
	return user.to_dict()

def get_guid(domainid, guid):
	db = current_app.db
	for user in db.session.query(JackDawADOU).filter_by(objectGUID = guid).filter(JackDawADOU.ad_id == domainid).all():
		return user.to_dict()