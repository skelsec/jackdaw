
from flask_sqlalchemy import SQLAlchemy
from jackdaw.dbmodel.adou import JackDawADOU

def list_ous(domainid):
    db = SQLAlchemy()
    domains = []
    for uid, sid, name in db.session\
                            .query(JackDawADOU)\
                                .filter_by(ad_id = domainid)\
                                .with_entities(JackDawADOU.id, JackDawADOU.sid, JackDawADOU.sAMAccountName)\
                                .all():
        domains.append((uid, sid, name))
    return domains

def get(domainid, ouid):
    db = SQLAlchemy()
    user = db.session.query(JackDawADOU).get(ouid)
    return user.to_dict()

def get_sid(domainid, sid):
    db = SQLAlchemy()
    for user in db.session.query(JackDawADOU).filter_by(sid = sid).filter(JackDawADOU.ad_id == domainid).all():
        return user.to_dict()