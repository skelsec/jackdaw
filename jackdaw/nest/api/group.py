
from flask import current_app
from jackdaw.dbmodel.adgroup import JackDawADGroup

def list_groups(domainid, page, maxcnt):
	db = current_app.db
	res = {
		'res' : [],
		'page': {},
	}
	qry = db.session.query(
        JackDawADGroup
        ).filter_by(ad_id = domainid
        ).with_entities(
            JackDawADGroup.id, 
            JackDawADGroup.sid, 
            JackDawADGroup.sAMAccountName
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
    user = db.session.query(JackDawADGroup).get(groupid)
    return user.to_dict()

def get_sid(domainid, sid):
    db = current_app.db
    for user in db.session.query(JackDawADGroup).filter_by(sid = sid).filter(JackDawADGroup.ad_id == domainid).all():
        return user.to_dict()