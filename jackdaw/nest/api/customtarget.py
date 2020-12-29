from flask import current_app
from jackdaw.dbmodel.customtarget import CustomTarget
import string

def store(data):
	hostname = data['hostname']
	description = data['description']

	db = current_app.db
	sc = CustomTarget(hostname, description, linksid = None, ownerid=None) #TODO: fill out owner id
	db.session.add(sc)
	db.session.commit()
	db.session.refresh(sc)
	return sc.id


def list():
	# ownerid is currently not implemented, but it should be added as soon as possible!
	db = current_app.db
	creds = []
	ownerid = None
	for res in db.session.query(CustomTarget).filter_by(ownerid = ownerid).all():
		creds.append(
			{
				'id' : res.id, 
				'hostname' : res.hostname, 
				'description' : res.description
			}
		)
	
	return creds
