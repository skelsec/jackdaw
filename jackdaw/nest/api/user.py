
from flask import current_app
from jackdaw.dbmodel.aduser import JackDawADUser

def list_users(domainid):
    db = current_app.db
    domains = []
    for uid, sid, name in db.session\
                            .query(JackDawADUser)\
                                .filter_by(ad_id = domainid)\
                                .with_entities(JackDawADUser.id, JackDawADUser.objectSid, JackDawADUser.sAMAccountName)\
                                .all():
        domains.append((uid, sid, name))
    return domains

def get(domainid, userid):
    db = current_app.db
    user = db.session.query(JackDawADUser).get(userid)
    return user.to_dict()

def get_sid(domainid, usersid):
    db = current_app.db
    for user in db.session.query(JackDawADUser).filter_by(objectSid = usersid).filter(JackDawADUser.ad_id == domainid).all():
        return user.to_dict()

def filter(domainid, proplist):
    #TODO: add other properties to search for!
    db = current_app.db
    query = db.session.query(JackDawADUser).filter_by(ad_id = domainid)
    for elem in proplist:
        if 'sAMAccountName' in elem:
            query = query.filter(JackDawADUser.sAMAccountName == elem['sAMAccountName'])
    
    user = query.first()
    if user is None:
        return {}
    return user.to_dict()