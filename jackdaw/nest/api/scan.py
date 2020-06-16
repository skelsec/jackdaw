


import connexion
from flask import current_app

from aiosmb.commons.connection.url import SMBConnectionURL
from msldap.commons.url import MSLDAPURLDecoder
from jackdaw.gatherer.smb.smb import SMBGatherer
from jackdaw.gatherer.ldap.aioldap import LDAPGatherer


def scan_enum(params):
	db_conn = current_app.config['SQLALCHEMY_DATABASE_URI']

	ldap_url = params['ldap_url']
	smb_url = params['smb_url']
	ldap_workers = params['ldap_workers']
	smb_workers = params['smb_workers']

	smb_mgr = SMBConnectionURL(smb_url)
	ldap_mgr = MSLDAPURLDecoder(ldap_url)

	mgr = LDAPGatherer(db_conn, ldap_mgr, agent_cnt=ldap_workers)
	adifo_id = mgr.run()
	#print('ADInfo entry successfully created with ID %s' % adifo_id)
		
	mgr = SMBGatherer(smb_mgr, worker_cnt=smb_workers)
	mgr.gathering_type = ['all']
	mgr.db_conn = db_conn
	mgr.target_ad = adifo_id
	mgr.run()

	return {'adifo_id' : adifo_id}
