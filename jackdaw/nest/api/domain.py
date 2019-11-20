
from flask_sqlalchemy import SQLAlchemy
from jackdaw.dbmodel.adinfo import JackDawADInfo
from flask import current_app

def list_domains(page, maxcnt):
	db = current_app.db
	res = {
		'res' : [],
		'page': {},
	}
	qry = db.session.query(
		JackDawADInfo
		).with_entities(
			JackDawADInfo.id, 
			JackDawADInfo.distinguishedName, 
			JackDawADInfo.fetched_at
			)
		
	qry = qry.paginate(page = page, max_per_page = maxcnt)
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
		current_page=qry.page,
		per_page=qry.per_page
	)

	res['res'] = domains
	res['page'] = page

	return res

def get(domainid):
	db = current_app.db
	adinfo = db.session.query(JackDawADInfo).get(domainid)
	return adinfo.to_dict()
