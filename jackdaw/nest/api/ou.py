
from flask_sqlalchemy import SQLAlchemy
from jackdaw.dbmodel.adou import JackDawADOU

def list_ous(domainid):
    db = SQLAlchemy()
    domains = []
    for uid, guid, ou in db.session\
                            .query(JackDawADOU)\
                                .filter_by(ad_id = domainid)\
                                .with_entities(JackDawADOU.id, JackDawADOU.objectGUID, JackDawADOU.ou)\
                                .all():
        domains.append((uid, guid, ou))
    return domains

def get(domainid, ouid):
    db = SQLAlchemy()
    user = db.session.query(JackDawADOU).get(ouid)
    return user.to_dict()

def get_guid(domainid, guid):
    db = SQLAlchemy()
    for user in db.session.query(JackDawADOU).filter_by(objectGUID = guid).filter(JackDawADOU.ad_id == domainid).all():
        return user.to_dict()