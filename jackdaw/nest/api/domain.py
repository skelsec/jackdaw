
from flask_sqlalchemy import SQLAlchemy
from jackdaw.dbmodel.adinfo import JackDawADInfo

def list_domains():
    db = SQLAlchemy()
    domains = []
    for did, distinguishedName, creation in db.session.query(JackDawADInfo).with_entities(JackDawADInfo.id, JackDawADInfo.distinguishedName, JackDawADInfo.fetched_at).all():
        name = distinguishedName.replace('DC=','')
        name = name.replace(',','.')
        domains.append((did, name, creation))
    return domains

def get(domainid):
    db = SQLAlchemy()
    adinfo = db.session.query(JackDawADInfo).get(domainid)
    return adinfo.to_dict()
