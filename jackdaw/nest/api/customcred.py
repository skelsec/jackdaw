from flask import current_app
from jackdaw.dbmodel.customcred import CustomCred
import string

def store(data):
	username = data['username']
	domain = data.get('domain', None)
	secret = data['secret']
	stype = data['stype']
	description = data['description']
	if domain == '':
		domain = None

	db = current_app.db
	sc = CustomCred(username, stype, secret, description, domain = domain, ownerid=None) #TODO: fill out owner id
	db.session.add(sc)
	db.session.commit()
	db.session.refresh(sc)
	return sc.id


def list():
	# ownerid is currently not implemented, but it should be added as soon as possible!
	db = current_app.db
	creds = []
	ownerid = None
	for res in db.session.query(CustomCred.id, CustomCred.description).filter_by(ownerid = ownerid).all():
		creds.append({
			'id' : res[0],
			'description' : res[1]
		})
	
	return creds
