
from flask import current_app
from jackdaw.dbmodel.aduser import ADUser

def list_users(domainid, page, maxcnt):
	db = current_app.db
	res = {
		'res' : [],
		'page': {},
	}
	qry = db.session.query(
        ADUser
        ).filter_by(ad_id = domainid
        ).with_entities(
            ADUser.id, 
            ADUser.objectSid, 
            ADUser.sAMAccountName
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

def get(domainid, userid):
    db = current_app.db
    user = db.session.query(ADUser).get(userid)
    return user.to_dict()

def get_sid(domainid, usersid):
    db = current_app.db
    for user in db.session.query(ADUser).filter_by(objectSid = usersid).filter(ADUser.ad_id == domainid).all():
        return user.to_dict()

def get_sam(domainid, sam):
    db = current_app.db
    for user in db.session.query(ADUser).filter_by(sAMAccountName = sam).filter(ADUser.ad_id == domainid).all():
        return user.to_dict()

def filter(domainid, proplist):
    #TODO: add other properties to search for!
    db = current_app.db
    query = db.session.query(ADUser).filter_by(ad_id = domainid)
    for elem in proplist:
        if 'sAMAccountName' in elem:
            query = query.filter(ADUser.sAMAccountName == elem['sAMAccountName'])
    
    user = query.first()
    if user is None:
        return {}
    return user.to_dict()