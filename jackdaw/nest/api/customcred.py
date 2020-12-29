from flask import current_app
from jackdaw.dbmodel.storedcreds import StoredCred
import string

def store(data):
	username = data['username']
	domain = data.get('domain', None)
	password = data['password']
	description = data['description']
	if domain == '':
		domain = None

	db = current_app.db
	sc = StoredCred(username, password, description, domain = domain, ownerid=None) #TODO: fill out owner id
	db.session.add(sc)
	db.session.commit()
	db.session.refresh(sc)
	return sc.id


def list():
	# ownerid is currently not implemented, but it should be added as soon as possible!
	db = current_app.db
	creds = []
	ownerid = None
	for res in db.session.query(StoredCred.id, StoredCred.description).filter_by(ownerid = ownerid).all():
		creds.append({
			'id' : res[0],
			'description' : res[1]
		})
	
	return creds
