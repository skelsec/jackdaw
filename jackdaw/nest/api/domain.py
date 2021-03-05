
from flask_sqlalchemy import SQLAlchemy
from jackdaw.dbmodel.adinfo import ADInfo
from flask import current_app
from jackdaw.dbmodel.utils.pagination import paginate

def list_domains(page, maxcnt):
	db = current_app.db
	res = {
		'res' : [],
		'page': {},
	}
	qry = db.session.query(
		ADInfo
		).with_entities(
			ADInfo.id,
			ADInfo.distinguishedName, 
			ADInfo.fetched_at
			)
		
	qry = paginate(qry, page, maxcnt)
	domains = []
	for did, distinguishedName, creation in qry.items:
		name = distinguishedName.replace('DC=','')
		name = name.replace(',','.')
		domains.append(
			{
				'id': did,
				'name': name, 
				'creation' : creation
			}
		)

	page = dict(
		total=qry.total, 
		current_page=qry.next_page - 1 if qry.next_page is not None else 1,
		per_page=maxcnt#qry.per_page
	)

	res['res'] = domains
	res['page'] = page

	return res

def get(domainid):
	db = current_app.db
	adinfo = db.session.query(ADInfo).get(domainid)
	return adinfo.to_dict()

def get_sid(domainsid):
    db = current_app.db
    for domain in db.session.query(ADInfo).filter_by(objectSid = domainsid).all():
        return domain.to_dict()