
from flask import current_app
from jackdaw.dbmodel.adgroup import Group

def list_groups(domainid, page, maxcnt):
	db = current_app.db
	res = {
		'res' : [],
		'page': {},
	}
	qry = db.session.query(
        Group
        ).filter_by(ad_id = domainid
        ).with_entities(
            Group.id, 
            Group.objectSid, 
            Group.sAMAccountName
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

def get(domainid, groupid):
    db = current_app.db
    user = db.session.query(Group).get(groupid)
    return user.to_dict()

def get_sid(domainid, sid):
    db = current_app.db
    for user in db.session.query(Group).filter_by(objectSid = sid).filter(Group.ad_id == domainid).all():
        return user.to_dict()