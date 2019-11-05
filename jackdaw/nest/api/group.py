
from flask import current_app
from jackdaw.dbmodel.adgroup import JackDawADGroup

def list_groups(domainid):
    db = current_app.db
    domains = []
    for uid, sid, name in db.session\
                            .query(JackDawADGroup)\
                                .filter_by(ad_id = domainid)\
                                .with_entities(JackDawADGroup.id, JackDawADGroup.sid, JackDawADGroup.sAMAccountName)\
                                .all():
        domains.append((uid, sid, name))
    return domains

def get(domainid, groupid):
    db = current_app.db
    user = db.session.query(JackDawADGroup).get(groupid)
    return user.to_dict()

def get_sid(domainid, sid):
    db = current_app.db
    for user in db.session.query(JackDawADGroup).filter_by(sid = sid).filter(JackDawADGroup.ad_id == domainid).all():
        return user.to_dict()