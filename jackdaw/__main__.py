#!/usr/bin/env python3
#
# Author:
#  Tamas Jos (@skelsec)
#

import sys
import logging
import asyncio

from sqlalchemy import exc

from aiosmb import logger as smblogger
from msldap import logger as msldaplogger

from jackdaw.dbmodel import create_db, get_session
from jackdaw.gatherer.smb.smb import SMBGathererManager
from jackdaw.gatherer.smb.smb_file import SMBShareGathererSettings, ShareGathererManager

from jackdaw._version import __banner__
from jackdaw import logger as jdlogger
from jackdaw.gatherer.ldap.aioldap import LDAPEnumeratorManager
from jackdaw.utils.argshelper import construct_ldapdef, construct_smbdef
from jackdaw.credentials.credentials import JackDawCredentials
from aiosmb.commons.connection.url import SMBConnectionURL
from msldap.commons.url import MSLDAPURLDecoder


async def run(args):
	print(__banner__)
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
		adifo_id = await mgr.run()
		jdlogger.info('ADInfo entry successfully created with ID %s' % adifo_id)
		
		mgr = SMBGathererManager(smb_mgr, worker_cnt=args.smb_workers, queue_size = args.smb_queue_size)
		mgr.gathering_type = ['all']
		mgr.db_conn = db_conn
		mgr.target_ad = adifo_id
		await mgr.run()

		if args.smb_share_enum is True:
			settings_base = SMBShareGathererSettings(adifo_id, smb_mgr, None, None, None)
			settings_base.dir_depth = args.smb_folder_depth
			mgr = ShareGathererManager(settings_base, db_conn = db_conn, worker_cnt = args.smb_workers)
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
		ldap_conn = ldap_mgr.get_client()
	
		mgr = LDAPEnumeratorManager(db_conn, ldap_mgr, agent_cnt=args.ldap_workers, queue_size=args.ldap_queue_size)
		adifo_id = await mgr.run()
		jdlogger.info('ADInfo entry successfully created with ID %s' % adifo_id)
		
	elif args.command in ['shares', 'sessions', 'localgroups']:
		smb_mgr = construct_smbdef(args)
		mgr = SMBGathererManager(smb_mgr, worker_cnt=args.smb_workers, queue_size = args.smb_queue_size)
		mgr.gathering_type = [args.command]
		mgr.db_conn = db_conn
		mgr.lookup_ad = args.lookup_ad
		
		if args.ldap_url:
			ldap_mgr = construct_ldapdef(args)
			ldap_conn = ldap_mgr.get_client()
			mgr.ldap_conn = ldap_conn
		
		if args.ad_id:
			mgr.target_ad = args.ad_id
		
		if args.target_file:
			mgr.targets_file = args.target_file
		
		await mgr.run()

	elif args.command == 'files':
		if args.src == 'domain':
			if not args.ad_id:
				raise Exception('ad-id parameter is mandatory in ldap mode')
			
			mgr = SMBConnectionURL(args.smb_url)
			settings_base = SMBShareGathererSettings(args.ad_id, mgr, None, None, None)
			settings_base.dir_depth = args.smb_folder_depth
			settings_base.dir_with_sd = args.with_sid
			settings_base.file_with_sd = args.with_sid

			mgr = ShareGathererManager(settings_base, db_conn = db_conn, worker_cnt = args.smb_workers)
			mgr.run()

	#	elif args.src == 'file':
	#		if not args.target_file:
	#			raise Exception('target-file parameter is mandatory in file mode')
	#		
	#		args.target_file
	#		args.lookup_ad
	#		args.with_sid
	#		args.smb_workers
	#
	#	elif args.src == 'ldap':
	#		if not args.ldap_url:
	#			raise Exception('ldap-url parameter is mandatory in ldap mode')
	#		args.lookup_ad
	#		args.with_sid
	#		args.smb_workers
	#
	#	
	#
	#	elif args.src == 'cmd':
			
		
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
	ldap_group.add_argument('--ldap-workers', type=int, default = 4, help='LDAP worker count for parallelization')
	ldap_group.add_argument('--ldap-queue-size', type=int, default = 100000, help='LDAP worker queue max size.')
	
	enum_group = subparsers.add_parser('enum', formatter_class=argparse.RawDescriptionHelpFormatter, help='Enumerate all stuffs', epilog = MSLDAPURLDecoder.help_epilog)
	enum_group.add_argument('ldap_url',  help='Connection specitication in URL format')
	enum_group.add_argument('smb_url',  help='Connection specitication in URL format')
	enum_group.add_argument('-q', '--same-query', action='store_true', help='Use the same query for LDAP as for SMB. LDAP url must still be present, but without a query')
	enum_group.add_argument('--ldap-workers', type=int, default = 4, help='LDAP worker count for parallelization')
	enum_group.add_argument('--ldap-queue-size', type=int, default = 100000, help='LDAP worker queue max size.')
	enum_group.add_argument('--smb-workers', type=int, default = 50, help='SMB worker count for parallelization')
	enum_group.add_argument('--smb-queue-size', type=int, default = 100000, help='SMB worker queue max size.')
	enum_group.add_argument('--smb-folder-depth', type=int, default = 1, help='Files enumeration folder depth')
	enum_group.add_argument('--smb-share-enum', action='store_true', help='Enables file enumeration in shares')
	
	share_group = subparsers.add_parser('shares', help='Enumerate shares on target')
	share_group.add_argument('smb_url',  help='Credential specitication in URL format')
	share_group.add_argument('--smb-queue-size', type=int, default = 100000, help='SMB worker queue max size.')
	share_group.add_argument('-t', '--target-file', help='taget file with hostnames. One per line.')
	share_group.add_argument('-l', '--ldap-url', help='ldap_connection_string. Use this to get targets from the domain controller')
	share_group.add_argument('-q', '--same-query', action='store_true', help='Use the same query for LDAP as for SMB. LDAP url must still be present, but without a query')
	share_group.add_argument('-d', '--ad-id', help='ID of the domainfo to poll targets rom the DB')
	share_group.add_argument('-i', '--lookup-ad', help='ID of the domainfo to look up comupter names. Advisable to set for LDAP and file pbased targets')
	share_group.add_argument('--smb-workers', type=int, default = 50, help='SMB worker count for parallelization')
	
	files_group = subparsers.add_parser('files', help='Enumerate files on targets')
	#files_group.add_argument('src', choices=['file', 'ldap', 'domain', 'cmd'])
	files_group.add_argument('src', choices=['domain'])
	files_group.add_argument('smb_url',  help='Credential specitication in URL format')
	#files_group.add_argument('-l', '--ldap-url', help='ldap_connection_string. Use this to get targets from the domain controller')
	files_group.add_argument('-d', '--ad-id', help='ID of the domainfo to poll targets from the DB')
	files_group.add_argument('-s', '--with-sid', action='store_true', help='Also fetches the SId for each file and folder')	
	#files_group.add_argument('-i', '--lookup-ad', help='ID of the domainfo to look up comupter names. Advisable to set for LDAP and file pbased targets')
	#files_group.add_argument('-t', '--target-file', help='taget file with hostnames. One per line.')
	files_group.add_argument('--smb-folder-depth', type=int, default = 1, help='Recursion depth for folder enumeration')
	files_group.add_argument('--smb-workers', type=int, default = 50, help='SMB worker count for parallelization. Read: connection/share')
	files_group.add_argument('--smb-queue-size', type=int, default = 100000, help='SMB worker queue max size.')
	
	

	localgroup_group = subparsers.add_parser('localgroups', help='Enumerate local group memberships on target')
	localgroup_group.add_argument('smb_url',  help='Credential specitication in URL format')
	localgroup_group.add_argument('-t', '--target-file', help='taget file with hostnames. One per line.')
	localgroup_group.add_argument('-l', '--ldap-url', help='ldap_connection_string. Use this to get targets from the domain controller')
	localgroup_group.add_argument('-d', '--ad-id', help='ID of the domainfo to poll targets rom the DB')
	localgroup_group.add_argument('-i', '--lookup-ad', help='ID of the domainfo to look up comupter names. Advisable to set for LDAP and file pbased targets')
	localgroup_group.add_argument('--smb-queue-size', type=int, default = 100000, help='SMB worker queue max size.')
	localgroup_group.add_argument('--smb-workers', type=int, default = 50, help='SMB worker count for parallelization.')
	
	session_group = subparsers.add_parser('sessions', help='Enumerate connected sessions on target')
	session_group.add_argument('smb_url',  help='Credential specitication in URL format')
	session_group.add_argument('-t', '--target-file', help='taget file with hostnames. One per line.')
	session_group.add_argument('-l', '--ldap-url', help='ldap_connection_string. Use this to get targets from the domain controller')
	session_group.add_argument('-d', '--ad-id', help='ID of the domainfo to poll targets rom the DB')
	session_group.add_argument('-i', '--lookup-ad', help='ID of the domainfo to look up comupter names. Advisable to set for LDAP and file pbased targets')
	session_group.add_argument('--smb-queue-size', type=int, default = 100000, help='SMB worker queue max size.')
	session_group.add_argument('--smb-workers', type=int, default = 50, help='SMB worker count for parallelization.')
	
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

	asyncio.run(run(args))

if __name__ == '__main__':
	main()
