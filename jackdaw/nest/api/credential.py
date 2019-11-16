
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from jackdaw.dbmodel.credential import Credential
from jackdaw.dbmodel.hashentry import HashEntry
from jackdaw.dbmodel.netsession import NetSession
from jackdaw.dbmodel.adcomp import JackDawADMachine
from jackdaw.dbmodel.aduser import JackDawADUser
from flask import current_app
import connexion

def impacket_upload(domainid):
    db = current_app.db
    file_to_upload = connexion.request.files['file_to_upload']
    #print(file_to_upload.read())
    ctr = 0
    fail = 0
    for cred in Credential.from_impacket_stream(file_to_upload.stream, domainid):
        try:
            print(cred)
            db.session.add(cred)
            db.session.commit()
            ctr += 1
        except IntegrityError:
            db.session.rollback()
            fail += 1

    return {'new' : ctr, 'duplicates' : fail }

def lsass_upload(domainid, computername = None):
    db = current_app.db
    file_to_upload = connexion.request.files['file_to_upload']
    #print(file_to_upload.read())
    ctr = 0
    fail = 0
    ctr_plain = 0
    fail_plain = 0
    for cred, plaintext, sid in Credential.from_lsass_stream(file_to_upload.stream, domainid):
        try:
            db.session.add(cred)
            db.session.commit()
            ctr += 1
        except IntegrityError:
            db.session.rollback()
            fail += 1

        if plaintext is not None and len(plaintext) > 0:
            he = HashEntry(plaintext, nt_hash = cred.nt_hash)
            try:
                db.session.add(he)
                db.session.commit()
                ctr_plain += 1
            except IntegrityError:
                db.session.rollback()
                fail_plain += 1

        if computername is not None:

            cname = computername
            if computername[-1] != '$':
                cname = computername + '$'
            comp = db.session.query(JackDawADMachine).filter_by(ad_id = domainid).filter(JackDawADMachine.sAMAccountName == cname).first()
            #print('COMP %s' % comp)
            if comp is None:
                continue
            user = db.session.query(JackDawADUser.sAMAccountName).filter_by(ad_id = domainid).filter(JackDawADUser.objectSid == sid).first()
            #print('USER %s' % user)
            #print('SID %s' % sid )
            if user is None:
                continue

            sess = NetSession()
            sess.machine_id = comp.id
            sess.source = comp.sAMAccountName
            sess.username = user.sAMAccountName
            try:
                db.session.add(sess)
                db.session.commit()
            except IntegrityError:
                db.session.rollback()


    return {'new' : ctr, 'duplicates' : fail, 'pwnew' : ctr_plain, 'pwduplicates' :  fail_plain }

def aiosmb_upload(domainid):
    db = current_app.db
    file_to_upload = connexion.request.files['file_to_upload']
    #print(file_to_upload.read())
    ctr = 0
    fail = 0
    ctr_plain = 0
    fail_plain = 0
    for cred, plaintext in Credential.from_aiosmb_stream(file_to_upload.stream, domainid):
        try:
            db.session.add(cred)
            db.session.commit()
            ctr += 1
        except IntegrityError:
            db.session.rollback()
            fail += 1

        if plaintext is not None and len(plaintext) > 0:
            he = HashEntry(plaintext, nt_hash = cred.nt_hash)
            try:
                db.session.add(he)
                db.session.commit()
                ctr_plain += 1
            except IntegrityError:
                db.session.rollback()
                fail_plain += 1

    return {'new' : ctr, 'duplicates' : fail, 'pwnew' : ctr_plain, 'pwduplicates' :  fail_plain }