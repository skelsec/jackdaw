
import connexion

from sqlalchemy.exc import IntegrityError
from jackdaw.dbmodel.credential import Credential
from jackdaw.dbmodel.hashentry import HashEntry
from jackdaw.dbmodel.netsession import NetSession
from jackdaw.dbmodel.adcomp import Machine
from jackdaw.dbmodel.aduser import ADUser
from jackdaw.credentials.credentials import JackDawCredentials
from flask import current_app

try:
	from pypykatz.utils.crypto.winhash import LM, NT
except ImportError:
	print('[JACKDAW] pypykatz not installed! storing creds will not work')



def impacket_upload(domainid):
	db = current_app.db
	file_to_upload = connexion.request.files['file_to_upload']
	#print(file_to_upload.read())
	ctr = 0
	fail = 0
	for cred in Credential.from_impacket_stream(file_to_upload.stream, domainid):
		try:
			db.session.add(cred)
			db.session.commit()
			ctr += 1
		except Exception as e:
			print(e)
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
			comp = db.session.query(Machine).filter_by(ad_id = domainid).filter(Machine.sAMAccountName == cname).first()
			#print('COMP %s' % comp)
			if comp is None:
				continue
			user = db.session.query(ADUser.sAMAccountName).filter_by(ad_id = domainid).filter(ADUser.objectSid == sid).first()
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
		if cred is None:
			continue
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

def potfile_upload():
	disable_usercheck = False
	disable_passwordcheck = False
	file_to_upload = connexion.request.files['file_to_upload']

	db = current_app.db
	creds = JackDawCredentials(None, db_session = db.session)
	gen = HashEntry.from_potfile_stream(file_to_upload.stream)

	creds.add_cracked_passwords_gen(gen, disable_usercheck, disable_passwordcheck)
	

	return {}

def passwords_upload(passwords):
	def pwit(passwords):
		for pw in passwords:
			nt_hash = NT(pw).hex()
			print(pw)
			print(nt_hash)
			yield HashEntry(pw, nt_hash=nt_hash)
	
	db = current_app.db
	disable_usercheck = False
	disable_passwordcheck = False

	gen = pwit(passwords)
	creds = JackDawCredentials(None, db_session = db.session)
	creds.add_cracked_passwords_gen(gen, disable_usercheck, disable_passwordcheck)

	return {}

def passwords_upload_file():
	def pwit(fs):
		for line in fs:
			line = line.decode()
			line = line.strip()

			nt_hash = NT(line).hex()
			yield HashEntry(line, nt_hash=nt_hash)
	
	file_to_upload = connexion.request.files['file_to_upload']
	db = current_app.db
	disable_usercheck = False
	disable_passwordcheck = False

	gen = pwit(file_to_upload.stream)
	creds = JackDawCredentials(None, db_session = db.session)
	creds.add_cracked_passwords_gen(gen, disable_usercheck, disable_passwordcheck)

	return {}

def get_uncracked_current(domainid, hashtype = 'nt'):
	hashtype = hashtype.upper()
	db = current_app.db
	creds = JackDawCredentials(None, domain_id = domainid, db_session = db.session)
	hashes = []
	for data in creds.get_uncracked_hashes(hashtype, False):
		hashes.append(data)
	return hashes, 200

def get_uncracked_all(domainid, hashtype = 'nt'):
	hashtype = hashtype.upper()
	db = current_app.db
	creds = JackDawCredentials(None, domain_id = domainid, db_session = db.session)
	hashes = []
	for data in creds.get_uncracked_hashes(hashtype, True):
		hashes.append(data)
	return hashes, 200

def get_cracked_users(domainid):
	db = current_app.db
	creds = JackDawCredentials(None, domain_id = domainid, db_session = db.session)
	rows = creds.get_cracked_users()
	return rows, 200

def get_pwsharing(domainid):
	db = current_app.db
	creds = JackDawCredentials(None, domain_id = domainid, db_session = db.session)
	pw_sharing_total, pw_sharing_cracked, pw_sharing_notcracked, new_pwshare = creds.get_pwsharing()
	return {
		'pw_sharing_total' : pw_sharing_total, 
		'pw_sharing_cracked' : pw_sharing_cracked,
		'pw_sharing_notcracked' : pw_sharing_notcracked,
		'pwsharing_users' : new_pwshare
	}

def get_stats(domainid):
	db = current_app.db
	creds = JackDawCredentials(None, domain_id = domainid, db_session = db.session)
	res = creds.cracked_stats()
	return res