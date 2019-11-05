
from flask import current_app
from jackdaw.dbmodel.adcomp import JackDawADMachine

def list_machines(domainid):
    db = current_app.db
    domains = []
    for uid, sid, name in db.session\
                            .query(JackDawADMachine)\
                                .filter_by(ad_id = domainid)\
                                .with_entities(JackDawADMachine.id, JackDawADMachine.objectSid, JackDawADMachine.sAMAccountName)\
                                .all():
        domains.append((uid, sid, name))
    return domains

def get(domainid, machineid):
    db = current_app.db
    machine = db.session.query(JackDawADMachine).get(machineid)
    return machine.to_dict()

def get_sid(domainid, sid):
    db = current_app.db
    for machine in db.session.query(JackDawADMachine).filter_by(objectSid = sid).filter(JackDawADMachine.ad_id == domainid).all():
        return machine.to_dict()
