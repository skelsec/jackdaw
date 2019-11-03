
from flask_sqlalchemy import SQLAlchemy
from jackdaw.dbmodel.aduser import JackDawADUser

def list_users(domainid):
    db = SQLAlchemy()
    domains = []
    for uid, sid, name in db.session\
                            .query(JackDawADUser)\
                                .filter_by(ad_id = domainid)\
                                .with_entities(JackDawADUser.id, JackDawADUser.objectSid, JackDawADUser.sAMAccountName)\
                                .all():
        domains.append((uid, sid, name))
    return domains

def get(domainid, userid):
    db = SQLAlchemy()
    user = db.session.query(JackDawADUser).get(userid)
    return user.to_dict()

def get_sid(domainid, usersid):
    db = SQLAlchemy()
    for user in db.session.query(JackDawADUser).filter_by(objectSid = usersid).filter(JackDawADUser.ad_id == domainid).all():
        return user.to_dict()
