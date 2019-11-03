
from flask_sqlalchemy import SQLAlchemy
from jackdaw.dbmodel.adgroup import JackDawADGroup

def list_groups(domainid):
    db = SQLAlchemy()
    domains = []
    for uid, gid, name in db.session\
                            .query(JackDawADGroup)\
                                .filter_by(ad_id = domainid)\
                                .with_entities(JackDawADGroup.id, JackDawADGroup.objectGUID, JackDawADGroup.sAMAccountName)\
                                .all():
        domains.append((uid, gid, name))
    return domains

def get(domainid, groupid):
    db = SQLAlchemy()
    user = db.session.query(JackDawADGroup).get(groupid)
    return user.to_dict()

def get_sid(domainid, gid):
    db = SQLAlchemy()
    for user in db.session.query(JackDawADGroup).filter_by(objectGUID = gid).filter(JackDawADGroup.ad_id == domainid).all():
        return user.to_dict()