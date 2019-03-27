from jackdaw.gatherer import *
from msldap.core.msldap import *
from jackdaw.dbmodel import *

if __name__ == '__main__':
	username = ''
	password = ''
	dc_ip = '10.10.10.2'
	db_conn = 'sqlite:///test.db'
	
	#MSLDAPUserCredential(domain=None, username= None, password = None, is_ntlm = False)
	#MSLDAP(login_credential, target_server, ldap_query_page_size = 1000, use_sspi = False)
	
	create_db(db_conn)
	target = MSLDAPTargetServer(dc_ip)
	ldap = MSLDAP(None, target, use_sspi = True)	
	ldapenum = LDAPEnumerator(db_conn, ldap)
	ldapenum.run()