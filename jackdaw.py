
import sys
from sqlalchemy import exc

from aiosmb import logger as smblogger

from msldap.core import *
from msldap import logger as msldaplogger

from jackdaw.dbmodel import *
from jackdaw.common.apq import AsyncProcessQueue
from jackdaw.gatherer.universal.smb import SMBGathererManager
#from jackdaw.representation.membership_graph import *
from jackdaw.representation.passwords_report import *
from jackdaw import logger as jdlogger
from jackdaw.gatherer.ldap import LDAPEnumerator


def ldap_from_string(ldap_connection_string):
	ldap_creds = MSLDAPCredential.from_connection_string(ldap_connection_string)
	ldap_target = MSLDAPTarget.from_connection_string(ldap_connection_string)
	return MSLDAPConnection(ldap_creds, ldap_target)

def main(args):
	if args.verbose == 0:
		logging.basicConfig(level=logging.INFO)
		jdlogger.setLevel(logging.INFO)
		msldaplogger.setLevel(logging.WARNING)
		smblogger.setLevel(logging.INFO)
		
	elif args.verbose == 1:
		logging.basicConfig(level=logging.DEBUG)
		jdlogger.setLevel(logging.DEBUG)
		msldaplogger.setLevel(logging.INFO)
		smblogger.setLevel(logging.INFO)
		
	elif args.verbose > 1:
		logging.basicConfig(level=1)
		msldaplogger.setLevel(logging.DEBUG)
		jdlogger.setLevel(1)
		smblogger.setLevel(1)
	
	if not args.sql:
		print('SQL connection identification is missing! You need to provide the --sql parameter')
		sys.exit()
	
	db_conn = args.sql
	create_db(db_conn)
	
	if args.command == 'enum':
		ldap_conn = ldap_from_string(args.ldap_connection_string)
		ldap_conn.connect()
	
		ldapenum = LDAPEnumerator(db_conn, ldap_conn)
		ldapenum.run()
		
		mgr = SMBGathererManager(args.credential_string)
		mgr.gathering_type = ['all']
		mgr.ldap_conn =  ldap_conn
		mgr.run()
		
	elif args.command == 'ldap':
		ldap_conn = ldap_from_string(args.ldap_connection_string)
		ldap_conn.connect()
	
		ldapenum = LDAPEnumerator(db_conn, ldap_conn)
		ldapenum.run()
		
	elif args.command in ['shares', 'sessions', 'localgroups']:
		mgr = SMBGathererManager(args.credential_string)
		mgr.gathering_type = [args.command]
		mgr.db_conn = db_conn
		
		if args.ldap:
			ldap_conn = ldap_from_string(args.ldap)
			ldap_conn.connect()
			mgr.ldap_conn =  ldap_conn
		
		elif args.target_file:
			mgr.targets_file = args.target_file
		
		mgr.run()
		
	elif args.command == 'plot':
		ad_id = 1
		mp = MembershipPlotter(db_conn)
		mp.get_network_data(ad_id)
		
		if args.plot_cmd == 'admins':
			network = mp.show_domain_admins()
			
		elif args.plot_cmd == 'src':
			network = mp.show_all_sources(args.source)
			
		elif args.plot_cmd == 'dst':
			network = mp.show_all_destinations(args.destination)
			
		elif args.plot_cmd == 'pp':
			network = mp.show_path(args.source, args.destination)
			
		else:
			raise Exception('Unknown graph command: %s' % args.plot_cmd)
		
		mp.plot(network)
	elif args.command == 'creds':
		ctr = 0
		ctr_fail = 0
		dbsession = get_session(db_conn)
		for cred in Credential.from_impacket_file(args.impacket_file):
			try:
				dbsession.add(cred)
				if ctr % 10000 == 0:
					print(ctr)
					dbsession.commit()
				
			except exc.IntegrityError as e:
				ctr_fail += 1
				dbsession.rollback()
				continue
			else:
				ctr += 1

		dbsession.commit()
		
		print('Added %d users. Failed inserts: %d' % (ctr, ctr_fail))
		
	elif args.command == 'passwords':
		mem_filter = {}
		dbsession = get_session(db_conn)
		ctr = 0
		for he in HashEntry.from_potfile(args.potfile):
			if he.nt_hash in mem_filter:
				continue
			mem_filter[he.nt_hash] = 1

			exists = False

			if args.disable_passwordcheck is False:
				#check if hash is already in HashEntry, if yes, skip
				if he.nt_hash:
					exists = dbsession.query(HashEntry.id).filter_by(nt_hash=he.nt_hash).scalar() is not None
				elif he.lm_hash:
					exists = dbsession.query(HashEntry.id).filter_by(lm_hash=he.lm_hash).scalar() is not None
				else:
					continue

				#print(exists)
				if exists is True:
					continue
			
			
			if args.disable_usercheck is False:
				#check if hash actually belongs to a user, if not, skip, otherwise put it in DB
				if he.nt_hash:
					qry = dbsession.query(Credential.nt_hash).filter(Credential.nt_hash == he.nt_hash)
				elif he.lm_hash:
					qry = dbsession.query(Credential.lm_hash).filter(Credential.lm_hash == he.lm_hash)
				else:
					continue
				
				exists = True if qry.first() else False
			
			if exists is True:
				try:
					dbsession.add(he)
					if ctr % 10000 == 0:
						print(ctr)
					#	dbsession.commit()
					dbsession.commit()
					

				except exc.IntegrityError as e:
					print(e)
					dbsession.rollback()
					continue
				else:
					ctr += 1

		dbsession.commit()
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
		report = PasswordsReport(db_conn, out_folder = 'test')
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
	ldap_group.add_argument('ldap_connection_string',  help='Connection specitication <domain>/<username>/<secret_type>:<secret>@<dc_ip_or_hostname_or_ldap_url>')
	
	enum_group = subparsers.add_parser('enum', formatter_class=argparse.RawDescriptionHelpFormatter, help='Enumerate all stuffs', epilog = MSLDAPCredential.help_epilog)
	enum_group.add_argument('ldap_connection_string',  help='Connection specitication <domain>/<username>/<secret_type>:<secret>@<dc_ip_or_hostname_or_ldap_url>')
	enum_group.add_argument('credential_string',  help='Credential specitication <domain>/<username>/<secret_type>:<secret>')
	
	share_group = subparsers.add_parser('shares', help='Enumerate shares on target')
	share_group.add_argument('credential_string',  help='Credential specitication <domain>/<username>/<secret_type>:<secret>')
	share_group.add_argument('-t', '--target-file', help='taget file with hostnames. One per line.')
	share_group.add_argument('-l', '--ldap', help='ldap_connection_string. Use this to get targets from the domain controller')
	
	
	localgroup_group = subparsers.add_parser('localgroups', help='Enumerate local group memberships on target')
	localgroup_group.add_argument('credential_string',  help='Credential specitication <domain>/<username>/<secret_type>:<secret>')
	localgroup_group.add_argument('-t', '--target-file', help='taget file with hostnames. One per line.')
	localgroup_group.add_argument('-l', '--ldap', help='ldap_connection_string. Use this to get targets from the domain controller')
	
	session_group = subparsers.add_parser('sessions', help='Enumerate connected sessions on target')
	session_group.add_argument('credential_string',  help='Credential specitication <domain>/<username>/<secret_type>:<secret>')
	session_group.add_argument('-t', '--target-file', help='taget file with hostnames. One per line.')
	session_group.add_argument('-l', '--ldap', help='ldap_connection_string. Use this to get targets from the domain controller')
	
	plot_group = subparsers.add_parser('plot', help='Plot AD object relationshipts')
	plot_group.add_argument('plot_cmd', default='admins', choices= ['admins', 'src', 'dst', 'pp'])
	plot_group.add_argument('-s', '--source', help='source node')
	plot_group.add_argument('-d', '--destination', help='destination node')
	
	credential_group = subparsers.add_parser('creds', help='Add credential information from impacket')
	credential_group.add_argument('impacket_file', help='file with LM and NT hashes, generated by impacket secretsdump.py')
	
	passwords_group = subparsers.add_parser('passwords', help='Add password information from hashcat potfile')
	passwords_group.add_argument('potfile', help='hashcat potfile with cracked hashes')
	passwords_group.add_argument('-t','--hash-type', default='NT', choices= ['NT', 'LM'])
	passwords_group.add_argument('--disable-usercheck', action='store_true', help = 'Disables the user pre-check when inserting to DB. All unique passwords will be uploaded.')
	passwords_group.add_argument('--disable-passwordcheck', action='store_true', help = 'Disables the password uniqueness check. WILL FAIL IF PW IS ALREADY IN THE DB.')
	
	uncracked_group = subparsers.add_parser('uncracked', help='Polls the DB for uncracked passwords')
	uncracked_group.add_argument('-t','--hash-type', default='NT', choices= ['NT', 'LM'])
	uncracked_group.add_argument('--history', action='store_true', help = 'Show password history hashes as well')	
	
	cracked_group = subparsers.add_parser('cracked', help='Polls the DB for cracked passwords')
	
	pwreport_group = subparsers.add_parser('pwreport', help='Generates credential statistics')
	pwreport_group.add_argument('-d','--domain-id', type=int, default = -1, help='Domain ID to identify the domain')
	pwreport_group.add_argument('-o','--out-file', help='Base file name to creates report files in')
	
	args = parser.parse_args()
	
	main(args)
	
