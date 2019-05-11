from sqlalchemy import exc
from jackdaw.gatherer import *
from msldap.core import *
from jackdaw.dbmodel import *
from jackdaw.representation.membership_graph import *
from jackdaw.representation.passwords_report import *

from jackdaw import logger as jdlogger
from msldap import logger as msldaplogger



def ldap_from_string(ldap_connection_string):
	ldap_creds = MSLDAPCredential.from_connection_string(ldap_connection_string)
	ldap_target = MSLDAPTarget.from_connection_string(ldap_connection_string)
	return MSLDAPConnection(ldap_creds, ldap_target)

def main(args):
	if args.verbose == 0:
		logging.basicConfig(level=logging.INFO)
		jdlogger.setLevel(logging.INFO)
		msldaplogger.setLevel(logging.WARNING)
		
	elif args.verbose == 1:
		logging.basicConfig(level=logging.DEBUG)
		jdlogger.setLevel(logging.DEBUG)
		msldaplogger.setLevel(logging.INFO)
		
	else:
		logging.basicConfig(level=1)
		msldaplogger.setLevel(logging.DEBUG)
		jdlogger.setLevel(1)
	
	db_conn = args.sql
	create_db(db_conn)
	
	if args.command == 'enum':
		ldap_conn = ldap_from_string(args.ldap_connection_string)
		ldap_conn.connect()
	
		ldapenum = LDAPEnumerator(db_conn, ldap_conn)
		ldapenum.run()
		
		se = ShareEnumerator(db_conn)
		se.load_targets_ldap(ldap_conn)
		se.run()
		
		sm = LocalGroupEnumerator(db_conn)
		sm.load_targets_ldap(ldap_conn)
		sm.run()
		
		sm = SessionMonitor(db_conn)
		sm.load_targets_ldap(ldap_conn)
		sm.run()
		
	elif args.command == 'ldap':
		ldap_conn = ldap_from_string(args.ldap_connection_string)
		ldap_conn.connect()
	
		ldapenum = LDAPEnumerator(db_conn, ldap_conn)
		ldapenum.run()
		
	elif args.command == 'share':
		se = ShareEnumerator(db_conn)
		if args.ldap:
			ldap_conn = ldap_from_string(args.ldap)
			ldap_conn.connect()
		
			se.load_targets_ldap(ldap_conn)
		
		elif args.target_file:
			se.load_targets_file(args.target_file)
		
		se.run()
		
	elif args.command == 'localgroup':
		sm = LocalGroupEnumerator(db_conn)
		
		if args.ldap:
			ldap_conn = ldap_from_string(args.ldap)
			ldap_conn.connect()
			sm.load_targets_ldap(ldap_conn)
		
		elif args.target_file:
			sm.load_targets_file(args.target_file)
		
		sm.run()

	elif args.command == 'session':
		sm = SessionMonitor(db_conn)
		if args.ldap:
			ldap_conn = ldap_from_string(args.ldap)
			ldap_conn.connect()
			
			sm.load_targets_ldap(ldap_conn)
		
		elif args.target_file:
			sm.load_targets_file(args.target_file)
			
		sm.run()
		
	elif args.command == 'plot':
		ad_id = 1
		mp = MembershipPlotter(db_conn)
		mp.get_network_data(ad_id)
		
		src = 'victim'
		dst = 'Domain Admins'
		network = mp.show_path(src, dst)
		mp.plot(network)
		
	elif args.command == 'creds':
		ctr = 0
		ctr_fail = 0
		dbsession = get_session(db_conn)
		for cred in Credential.from_impacket_file(args.impacket_file):
			try:
				dbsession.add(cred)
				dbsession.commit()
				
			except exc.IntegrityError as e:
				ctr_fail += 1
				dbsession.rollback()
				continue
			else:
				ctr += 1
		
		print('Added %d users. Failed inserts: %d' % (ctr, ctr_fail))
		
	elif args.command == 'passwords':
		dbsession = get_session(db_conn)
		ctr = 0
		for he in HashEntry.from_potfile(args.potfile):
			if he.nt_hash:
				qry = dbsession.query(Credential.nt_hash).filter(Credential.nt_hash == he.nt_hash)
			elif he.lm_hash:
				qry = dbsession.query(Credential.lm_hash).filter(Credential.lm_hash == he.lm_hash)
			else:
				continue
					
			if qry.first():
				try:
					dbsession.add(he)
					dbsession.commit()
				except exc.IntegrityError as e:
					dbsession.rollback()
					continue
				else:
					ctr += 1
					
		print('Added %d plaintext passwords to the DB' % ctr)
		
	elif args.command == 'uncracked':
		dbsession = get_session(db_conn)
		if args.hash_type == 'NT':
			qry = dbsession.query(Credential.nt_hash).outerjoin(HashEntry, Credential.nt_hash == HashEntry.nt_hash).filter(Credential.nt_hash != None).distinct(Credential.nt_hash)
		else:
			qry = dbsession.query(Credential.lm_hash).outerjoin(HashEntry, Credential.lm_hash == HashEntry.lm_hash).filter(Credential.lm_hash != None).distinct(Credential.lm_hash)
		
		if args.history == False:
			qry = qry.filter(Credential.history_no == 0)
			
		for some_hash in qry.all():
			print(some_hash[0])
			
	elif args.command == 'pwreport':
		report = PasswordsReport(db_conn)
		report.generate(args.domain_id)
		
	elif args.command == 'cracked':
		pass
	
	

if __name__ == '__main__':
	import argparse
	
	parser = argparse.ArgumentParser(description='Gather gather gather')
	parser.add_argument('-v', '--verbose', action='count', default=0, help='Increase verbosity, can be stacked')
	parser.add_argument('--sql', help='SQL connection string')
	
	subparsers = parser.add_subparsers(help = 'commands')
	subparsers.required = True
	subparsers.dest = 'command'
	
	ldap_group = subparsers.add_parser('ldap', formatter_class=argparse.RawDescriptionHelpFormatter, help='Enumerate potentially vulnerable users via LDAP', epilog = MSLDAPCredential.help_epilog)
	ldap_group.add_argument('ldap_connection_string',  help='LDAP connection specitication <domain>/<username>/<secret_type>:<secret>@<dc_ip_or_hostname_or_ldap_url>')
	
	enum_group = subparsers.add_parser('enum', formatter_class=argparse.RawDescriptionHelpFormatter, help='Enumerate all stuffs', epilog = MSLDAPCredential.help_epilog)
	enum_group.add_argument('ldap_connection_string',  help='LDAP connection specitication <domain>/<username>/<secret_type>:<secret>@<dc_ip_or_hostname_or_ldap_url>')
	
	
	share_group = subparsers.add_parser('share', help='Enumerate shares on target')
	share_group.add_argument('-t', '--target-file', help='taget file with hostnames. One per line.')
	share_group.add_argument('-l', '--ldap', help='ldap_connection_string. Use this to get targets from the domain controller')
	
	localgroup_group = subparsers.add_parser('localgroup', help='Enumerate local group memberships on target')
	localgroup_group.add_argument('-t', '--target-file', help='taget file with hostnames. One per line.')
	localgroup_group.add_argument('-l', '--ldap', help='ldap_connection_string. Use this to get targets from the domain controller')
	
	session_group = subparsers.add_parser('session', help='Enumerate connected sessions on target')
	session_group.add_argument('-t', '--target-file', help='taget file with hostnames. One per line.')
	session_group.add_argument('-l', '--ldap', help='ldap_connection_string. Use this to get targets from the domain controller')
	
	plot_group = subparsers.add_parser('plot', help='Plot AD object relationshipts')
	
	credential_group = subparsers.add_parser('creds', help='Add credential information from impacket')
	credential_group.add_argument('impacket_file', help='file with LM and NT hashes, generated by impacket secretsdump.py')
	
	passwords_group = subparsers.add_parser('passwords', help='Add password information from hashcat potfile')
	passwords_group.add_argument('potfile', help='hashcat potfile with cracked hashes')
	passwords_group.add_argument('-t','--hash-type', default='NT', choices= ['NT', 'LM'])
	
	uncracked_group = subparsers.add_parser('uncracked', help='Polls the DB for uncracked passwords')
	uncracked_group.add_argument('-t','--hash-type', default='NT', choices= ['NT', 'LM'])
	uncracked_group.add_argument('--history', action='store_true', help = 'Show password history hashes as well')	
	
	cracked_group = subparsers.add_parser('cracked', help='Polls the DB for cracked passwords')
	
	pwreport_group = subparsers.add_parser('pwreport', help='Generates credential statistics')
	pwreport_group.add_argument('-d','--domain-id', type=int, help='Domain ID to identify the domain')
	pwreport_group.add_argument('-o','--out-file', help='Base file name to creates report files in')
	
	args = parser.parse_args()
	
	main(args)
	