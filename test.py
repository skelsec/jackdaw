from jackdaw.gatherer import *
from msldap.core.msldap import *
from jackdaw.dbmodel import *
from jackdaw.representation.membership_graph import *

if __name__ == '__main__':
	username = ''
	password = ''
	dc_ip = '10.10.10.2'
	db_conn = 'sqlite:///E:\\test.db'
	
	#MSLDAPUserCredential(domain=None, username= None, password = None, is_ntlm = False)
	#MSLDAP(login_credential, target_server, ldap_query_page_size = 1000, use_sspi = False)
	
	create_db(db_conn)
	"""
	target = MSLDAPTargetServer(dc_ip)
	ldap = MSLDAP(None, target, use_sspi = True)	
	ldap.connect()
	
	ldapenum = LDAPEnumerator(db_conn, ldap)
	ldapenum.run()
	
	se = ShareEnumerator(db_conn)
	se.load_targets_ldap(ldap)
	se.run()

	sm = LocalGroupEnumerator(db_conn)
	sm.load_targets_ldap(ldap)
	sm.run()
	
	sm = SessionMonitor(db_conn)
	sm.load_targets_ldap(ldap)
	sm.run()
	"""
	mp = MembershipPlotter(db_conn)
	mp.run(1)