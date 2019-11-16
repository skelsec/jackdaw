
import sys
import logging

from sqlalchemy import exc

from aiosmb import logger as smblogger
from msldap import logger as msldaplogger

from jackdaw.dbmodel import create_db, get_session
from jackdaw.common.apq import AsyncProcessQueue
from jackdaw.common.proxy import ProxyConnection
from jackdaw.gatherer.universal.smb import SMBGathererManager

from jackdaw import logger as jdlogger
from jackdaw.gatherer.ldap_mp import LDAPEnumeratorManager
from jackdaw.utils.argshelper import *
from jackdaw.credentials.credentials import JackDawCredentials


def run(args):
	if args.verbose == 0:
		logging.basicConfig(level=logging.INFO)
		jdlogger.setLevel(logging.INFO)
		msldaplogger.setLevel(logging.WARNING)
		smblogger.setLevel(logging.CRITICAL)
		
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
	
	if args.command == 'enum':
		smb_mgr = construct_smbdef(args)
		ldap_mgr = construct_ldapdef(args)

		mgr = LDAPEnumeratorManager(db_conn, ldap_mgr, agent_cnt=args.ldap_workers)
		adifo_id = mgr.run()
		print('ADInfo entry successfully created with ID %s' % adifo_id)
		
		mgr = SMBGathererManager(smb_mgr, worker_cnt=args.smb_workers)
		mgr.gathering_type = ['all']
		mgr.db_conn = db_conn
		mgr.target_ad = adifo_id
		mgr.run()
	
	elif args.command == 'dbinit':
		create_db(db_conn)
	
	elif args.command == 'adinfo':
		session = get_session(db_conn)
		from jackdaw.dbmodel.adinfo import JackDawADInfo
		from jackdaw.utils.table import print_table
		
		rows = [['Ad ID', 'domain name', 'scantime']]
		for did, distinguishedName, creation in session.query(JackDawADInfo).with_entities(JackDawADInfo.id, JackDawADInfo.distinguishedName, JackDawADInfo.fetched_at).all():
			name = distinguishedName.replace('DC=','')
			name = name.replace(',','.')
			rows.append([str(did), name, creation.isoformat()])
		print_table(rows)
		
	elif args.command == 'ldap':
		ldap_mgr = construct_ldapdef(args)
		ldap_conn = ldap_mgr.get_connection()
		ldap_conn.connect()
	
		mgr = LDAPEnumeratorManager(db_conn, ldap_mgr, agent_cnt=args.ldap_workers)
		adifo_id = mgr.run()
		print('ADInfo entry successfully created with ID %s' % adifo_id)
		
	elif args.command in ['shares', 'sessions', 'localgroups']:
		smb_mgr = construct_smbdef(args)
		mgr = SMBGathererManager(smb_mgr)
		mgr.gathering_type = [args.command]
		mgr.db_conn = db_conn
		mgr.lookup_ad = args.lookup_ad
		
		if args.ldap_url:
			ldap_mgr = construct_ldapdef(args)
			ldap_conn = ldap_mgr.get_connection()
			ldap_conn.connect()
			mgr.ldap_conn = ldap_conn
		
		if args.ad_id:
			mgr.target_ad = args.ad_id
		
		if args.target_file:
			mgr.targets_file = args.target_file
		
		mgr.run()
		
	elif args.command == 'creds':
		creds = JackDawCredentials(args.db_conn, args.domain_id)
		creds.add_credentials_impacket(args.impacket_file)

		
	elif args.command == 'passwords':
		creds = JackDawCredentials(args.db_conn)
		creds.add_cracked_passwords(args.potfile, args.disable_usercheck, args.disable_passwordcheck)
		
	elif args.command == 'uncracked':
		creds = JackDawCredentials(args.db_conn, args.domain_id)
		creds.get_uncracked_hashes(args.hash_type, args.history)
		
	elif args.command == 'cracked':
		creds = JackDawCredentials(args.db_conn, args.domain_id)
		creds.get_cracked_info()

	elif args.command == 'nest':
		from jackdaw.nest.wrapper import NestServer

		debug = bool(args.verbose)

		server = NestServer(args.sql, bind_ip = args.ip, bind_port = args.port, debug = debug)
		server.run()
	
def main():
	import argparse
	
	parser = argparse.ArgumentParser(description='Gather gather gather')
	parser.add_argument('-v', '--verbose', action='count', default=0, help='Increase verbosity, can be stacked')
	parser.add_argument('--sql', help='SQL connection string. When using SQLITE it works best with FULL FILE PATH!!!')
	
	subparsers = parser.add_subparsers(help = 'commands')
	subparsers.required = True
	subparsers.dest = 'command'
	
	nest_group = subparsers.add_parser('nest', formatter_class=argparse.RawDescriptionHelpFormatter, help='Start the Nest server')
	nest_group.add_argument('--ip',  default = '127.0.0.1', help='IP address to listen on')
	nest_group.add_argument('--port',  type=int, default = 5000, help='IP address to listen on')

	adinfo_group = subparsers.add_parser('adinfo', help='Get a list of AD info entries')
	dbinit_group = subparsers.add_parser('dbinit', help='Creates database')
	

	ldap_group = subparsers.add_parser('ldap', formatter_class=argparse.RawDescriptionHelpFormatter, help='Enumerate potentially vulnerable users via LDAP', epilog = MSLDAPURLDecoder.help_epilog)
	ldap_group.add_argument('ldap_url',  help='Connection specitication in URL format')
	
	enum_group = subparsers.add_parser('enum', formatter_class=argparse.RawDescriptionHelpFormatter, help='Enumerate all stuffs', epilog = MSLDAPURLDecoder.help_epilog)
	enum_group.add_argument('ldap_url',  help='Connection specitication in URL format')
	enum_group.add_argument('smb_url',  help='Connection specitication in URL format')
	enum_group.add_argument('-q', '--same-query', action='store_true', help='Use the same query for LDAP as for SMB. LDAP url must still be present, but without a query')
	enum_group.add_argument('--ldap-workers', type=int, default = 4, help='LDAP worker count for parallelization')
	enum_group.add_argument('--smb-workers', type=int, default = 50, help='SMB worker count for parallelization')
	
	share_group = subparsers.add_parser('shares', help='Enumerate shares on target')
	share_group.add_argument('smb_url',  help='Credential specitication in URL format')
	share_group.add_argument('-t', '--target-file', help='taget file with hostnames. One per line.')
	share_group.add_argument('-l', '--ldap-url', help='ldap_connection_string. Use this to get targets from the domain controller')
	share_group.add_argument('-q', '--same-query', action='store_true', help='Use the same query for LDAP as for SMB. LDAP url must still be present, but without a query')
	share_group.add_argument('-d', '--ad-id', help='ID of the domainfo to poll targets rom the DB')
	share_group.add_argument('-i', '--lookup-ad', help='ID of the domainfo to look up comupter names. Advisable to set for LDAP and file pbased targets')
	
	localgroup_group = subparsers.add_parser('localgroups', help='Enumerate local group memberships on target')
	localgroup_group.add_argument('smb_url',  help='Credential specitication in URL format')
	localgroup_group.add_argument('-t', '--target-file', help='taget file with hostnames. One per line.')
	localgroup_group.add_argument('-l', '--ldap-url', help='ldap_connection_string. Use this to get targets from the domain controller')
	localgroup_group.add_argument('-d', '--ad-id', help='ID of the domainfo to poll targets rom the DB')
	localgroup_group.add_argument('-i', '--lookup-ad', help='ID of the domainfo to look up comupter names. Advisable to set for LDAP and file pbased targets')
	
	session_group = subparsers.add_parser('sessions', help='Enumerate connected sessions on target')
	session_group.add_argument('smb_url',  help='Credential specitication in URL format')
	session_group.add_argument('-t', '--target-file', help='taget file with hostnames. One per line.')
	session_group.add_argument('-l', '--ldap-url', help='ldap_connection_string. Use this to get targets from the domain controller')
	session_group.add_argument('-d', '--ad-id', help='ID of the domainfo to poll targets rom the DB')
	session_group.add_argument('-i', '--lookup-ad', help='ID of the domainfo to look up comupter names. Advisable to set for LDAP and file pbased targets')
	
	credential_group = subparsers.add_parser('creds', help='Add credential information from impacket')
	credential_group.add_argument('impacket_file', help='file with LM and NT hashes, generated by impacket secretsdump.py')
	credential_group.add_argument('-d','--domain-id', type=int, default = -1, help='Domain ID to identify the domain')
	
	passwords_group = subparsers.add_parser('passwords', help='Add password information from hashcat potfile')
	passwords_group.add_argument('potfile', help='hashcat potfile with cracked hashes')
	passwords_group.add_argument('--disable-usercheck', action='store_true', help = 'Disables the user pre-check when inserting to DB. All unique passwords will be uploaded.')
	passwords_group.add_argument('--disable-passwordcheck', action='store_true', help = 'Disables the password uniqueness check. WILL FAIL IF PW IS ALREADY IN THE DB.')
	
	uncracked_group = subparsers.add_parser('uncracked', help='Polls the DB for uncracked passwords')
	uncracked_group.add_argument('-t','--hash-type', default='NT', choices= ['NT', 'LM'])
	uncracked_group.add_argument('--history', action='store_true', help = 'Show password history hashes as well')
	uncracked_group.add_argument('-d','--domain-id', type=int, default = -1, help='Domain ID to identify the domain')
	
	cracked_group = subparsers.add_parser('cracked', help='Polls the DB for cracked passwords')
	cracked_group.add_argument('-d','--domain-id', type=int, default = -1, help='Domain ID to identify the domain')
	
	args = parser.parse_args()

	run(args)

if __name__ == '__main__':
	main()
	
