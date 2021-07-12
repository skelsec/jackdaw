import asyncio
import traceback
from jackdaw.dbmodel.adinfo import ADInfo
from jackdaw.nest.ws.protocol import *
import platform
import multiprocessing

from jackdaw import logger
from jackdaw.gatherer.gatherer import Gatherer
from jackdaw.nest.ws.protocol.agent.agent import NestOpAgent
from jackdaw.nest.ws.protocol.smb.smbfileres import NestOpSMBFileRes

from jackdaw.gatherer.progress import GathererProgressType

from jackdaw.dbmodel.adcomp import Machine
from jackdaw.dbmodel.dnslookup import DNSLookup
from jackdaw.dbmodel.credential import Credential
from jackdaw.dbmodel.storedcreds import StoredCred
from jackdaw.dbmodel.customtarget import CustomTarget

from aiosmb.commons.connection.target import SMBTarget, SMBConnectionProtocol, SMB2_NEGOTIATE_DIALTECTS_2
from aiosmb.commons.connection.credential import SMBCredential, SMBAuthProtocol, SMBCredentialsSecretType
from aiosmb.commons.connection.authbuilder import AuthenticatorBuilder
from aiosmb.connection import SMBConnection
from aiosmb.commons.interfaces.machine import SMBMachine

STANDARD_PROGRESS_MSG_TYPES = [
	GathererProgressType.BASIC,  
	GathererProgressType.SD,
	GathererProgressType.SDUPLOAD,
	GathererProgressType.MEMBERS,
	GathererProgressType.MEMBERSUPLOAD,
	GathererProgressType.SMB,
	GathererProgressType.KERBEROAST,
	GathererProgressType.SDCALC,
	GathererProgressType.SDCALCUPLOAD,
	GathererProgressType.INFO,
]


class JackDawAgent:
	def __init__(self, agent_id, agent_type, agent_platform, db_session, pid = 0, username = '', domain = '', logonserver = '', cpuarch = '', hostname = '', usersid = '', internal_id = None):
		self.agent_id = agent_id
		self.agent_type = agent_type
		self.platform = agent_platform
		self.pid = pid
		self.username = username
		self.domain = domain
		self.logonserver = logonserver
		self.cpuarch = cpuarch
		self.hostname = hostname
		self.usersid = usersid
		self.internal_id = internal_id
		self.connection_via = []
		self.db_session = db_session

	def get_list_reply(self, cmd):
		agent = NestOpAgent()
		agent.token = cmd.token
		agent.agentid = self.agent_id
		agent.agenttype = self.agent_type
		agent.platform = self.platform
		agent.pid = self.pid
		agent.username = self.username
		agent.domain = self.domain
		agent.logonserver = self.logonserver
		agent.cpuarch = self.cpuarch
		agent.hostname = self.hostname
		agent.usersid = self.usersid
		agent.internal_id = self.internal_id
		return agent

	def get_target_address(self, cmd):
		if cmd.hostname is not None and len(cmd.hostname) > 0 or cmd.ip is not None and len(cmd.ip) > 0:
			return cmd.hostname, cmd.ip
		else:
			return self.get_target_address_db(cmd.machine_ad_id, cmd.machine_sid)

	def get_stored_cred(self, cmd):
		domain = None
		username = None
		password = None

		print(cmd.__dict__)
		
		if cmd.username is not None and len(cmd.username) > 0:
			username = cmd.username
		if cmd.password is not None and len(cmd.password) > 0:
			password = cmd.password
		if cmd.domain is not None and len(cmd.domain) > 0:
			domain = cmd.domain
		
		if username == 'auto' and domain is None and cmd.user_ad_id is not None:
			adinfo = ADInfo.get(cmd.user_ad_id)
			domain = adinfo.name

		print(username)
		if username == 'auto' or username is not None:
			return True, domain, username, password

		return self.get_stored_cred_db(cmd.user_ad_id, cmd.user_sid)

	def get_target_address_db(self, ad_id, taget_sid):
		hostname = None
		if str(ad_id) == '0':
			res = self.db_session.query(CustomTarget).get(taget_sid)
			if res is not None:
				hostname = res.hostname
		else:
			res = self.db_session.query(Machine.dNSHostName).filter_by(objectSid = taget_sid).filter(Machine.ad_id == ad_id).first()
			if res is not None:
				hostname = res[0]
			else:
				res = self.db_session.query(DNSLookup.ip).filter_by(sid = taget_sid).filter(DNSLookup.ad_id == ad_id).first()
				if res is not None:
					hostname = res[0]

		print(hostname)
		return hostname, None

	def get_stored_cred_db(self, ad_id, user_sid):
		domain = None
		username = None
		password = None

		if str(ad_id) == '0':
			res = self.db_session.query(StoredCred).get(user_sid)
			
		else:
			res = self.db_session.query(Credential).filter_by(object_sid = user_sid).filter(Credential.ad_id == ad_id).first()
		
		if res is None:
			return False, None, None, None
		
		domain   = res.domain
		username = res.username
		password = res.password
		return True, domain, username, password

	def get_smb_connection(self, cmd):
		try:
			hostname, ip = self.get_target_address(cmd.target)
			res, domain, username, password = self.get_stored_cred(cmd.creds)
			if res is False:
				raise Exception('Could not find user creds!')
			
			target = SMBTarget(
				ip = ip,
				hostname = hostname, 
				timeout= 1,
				dc_ip = domain,
				protocol=SMBConnectionProtocol.TCP
			)
			target.preferred_dialects = SMB2_NEGOTIATE_DIALTECTS_2

			auth_type = SMBAuthProtocol.NTLM
			secret_type = SMBCredentialsSecretType.PASSWORD

			credential = SMBCredential(
				username = username, 
				domain = domain, 
				secret = password, 
				secret_type = secret_type, 
				authentication_type = auth_type, 
				settings = None, 
				target = target
			)
			print(target)
			print(credential)

			gssapi = AuthenticatorBuilder.to_spnego_cred(credential, target)
			connection = SMBConnection(gssapi, target)

			return connection, None
		except Exception as e:
			traceback.print_exc()
			return None, e

	async def run(self):
		#placeholder, might need it
		return

	async def do_smbfiles(self, cmd, out_q, cancel_token):
		try:
			connection, err = self.get_smb_connection(cmd)
			if err is not None:
				await out_q.put(NestOpErr(cmd.token, str(err)))
				return
			async with connection:
				_, err = await connection.login()
				if err is not None:
					raise err
				async with SMBMachine(connection) as machine:
					async for obj, otype, err in machine.enum_all_recursively(depth=cmd.depth):
						if otype[0].upper() in ['F', 'D']:
							reply = NestOpSMBFileRes()
							reply.token = cmd.token
							reply.machine_ad_id = None
							reply.machine_sid = None
							reply.otype = otype
							reply.unc_path = obj.unc_path
							await out_q.put(reply)

			await out_q.put(NestOpOK(cmd.token))
		except asyncio.CancelledError:
			return
		except Exception as e:
			traceback.print_exc()
			print('do_smbfiles error! %s' % e)
			await out_q.put(NestOpErr(cmd.token, str(e)))
		finally:
			cancel_token.set()

	async def __gathermonitor(self, cmd, results_queue, out_q):
		try:
			usernames_testing = []
			machine_sids_testing = []
			
			temp_tok_testing = None
			temp_adid_testing = None
			temp_started = False
			
			while True:
				try:
					msg = await results_queue.get()
					if msg is None:
						break
					
					#print(msg)
					if msg.type in STANDARD_PROGRESS_MSG_TYPES:
						##### TESTING
						temp_tok_testing = cmd.token
						temp_adid_testing = msg.adid
						
						######
						reply = NestOpGatherStatus()
						reply.token = cmd.token
						reply.current_progress_type = msg.type.value
						reply.msg_type = msg.msg_type.value
						reply.adid = msg.adid
						reply.domain_name = msg.domain_name
						reply.total = msg.total
						reply.step_size = msg.step_size
						reply.basic_running = []
						if msg.running is not None:
							reply.basic_running = [x for x in msg.running]
						reply.basic_finished = msg.finished
						reply.smb_errors = msg.errors
						reply.smb_sessions = msg.sessions
						reply.smb_shares = msg.shares
						reply.smb_groups = msg.groups
						await out_q.put(reply)
						#await self.websocket.send(reply.to_json())
						
						####TESTINGTESTING!!!!
						#if msg.type.value != 'LDAP_BASIC':
						#	if temp_started is False:
						#		asyncio.create_task(self.spam_sessions(temp_tok_testing, temp_adid_testing, machine_sids_testing, usernames_testing))
						#		temp_started = True
								
					elif msg.type == GathererProgressType.USER:
						usernames_testing.append(msg.data.sAMAccountName)
						reply = NestOpUserRes()
						reply.token = cmd.token
						reply.name = msg.data.sAMAccountName
						reply.adid = msg.data.ad_id
						reply.sid = msg.data.objectSid
						reply.kerberoast = 1 if msg.data.servicePrincipalName is not None else 0
						reply.asreproast = int(msg.data.UAC_DONT_REQUIRE_PREAUTH)
						reply.nopassw = int(msg.data.UAC_PASSWD_NOTREQD)
						reply.cleartext = int(msg.data.UAC_ENCRYPTED_TEXT_PASSWORD_ALLOWED)
						reply.smartcard = int(msg.data.UAC_SMARTCARD_REQUIRED)
						reply.active = int(msg.data.canLogon)
						reply.description = msg.data.description
						reply.is_admin = int(msg.data.adminCount) if msg.data.adminCount is not None else None
						
						await out_q.put(reply)
						#await self.websocket.send(reply.to_json())
					
					elif msg.type == GathererProgressType.MACHINE:
						machine_sids_testing.append(msg.data.objectSid)
						reply = NestOpComputerRes()
						reply.token = cmd.token
						reply.name = msg.data.sAMAccountName
						reply.adid = msg.data.ad_id
						reply.sid = msg.data.objectSid
						reply.domainname = msg.data.dNSHostName
						reply.osver = msg.data.operatingSystem
						reply.ostype = msg.data.operatingSystemVersion
						reply.description = msg.data.description
						if msg.data.UAC_SERVER_TRUST_ACCOUNT is True:
							reply.computertype = 'DOMAIN_CONTROLLER'
						elif msg.data.operatingSystem is not None:
							if msg.data.operatingSystem.lower().find('windows') != -1:
								if msg.data.operatingSystem.lower().find('server') != -1:
									reply.computertype = 'SERVER'
								else:
									reply.computertype = 'WORKSTATION'
							else:
								reply.computertype = 'NIX'
						else:
							reply.computertype = 'DUNNO'
						
						await out_q.put(reply)
						#await self.websocket.send(reply.to_json())
					
					elif msg.type == GathererProgressType.SMBLOCALGROUP:
						reply = NestOpSMBLocalGroupRes()
						reply.token = cmd.token
						reply.adid = msg.data.ad_id
						reply.machinesid = msg.data.machine_sid
						reply.usersid = msg.data.sid
						reply.groupname = msg.data.groupname
						#await self.websocket.send(reply.to_json())
						await out_q.put(reply)
					
					elif msg.type == GathererProgressType.SMBSHARE:
						reply = NestOpSMBShareRes()
						reply.token = cmd.token
						reply.adid = msg.data.ad_id
						reply.machinesid = msg.data.machine_sid
						reply.netname = msg.data.netname
						#await self.websocket.send(reply.to_json())
						await out_q.put(reply)
					
					elif msg.type == GathererProgressType.SMBSESSION:					
						reply = NestOpSMBSessionRes()
						reply.token = cmd.token
						reply.adid = msg.data.ad_id
						reply.machinesid = msg.data.machine_sid
						reply.username = msg.data.username
						await out_q.put(reply)
						#await self.websocket.send(reply.to_json())
					
					elif msg.type == GathererProgressType.GROUP:					
						reply = NestOpGroupRes()
						reply.token = cmd.token
						reply.adid = msg.data.ad_id
						reply.name = msg.data.sAMAccountName
						reply.dn = msg.data.dn
						reply.guid = msg.data.objectGUID
						reply.sid = msg.data.objectSid
						reply.description = msg.data.description
						#await self.websocket.send(reply.to_json())
						await out_q.put(reply)
						
				except asyncio.CancelledError:
					return
				except Exception as e:
					logger.exception('resmon processing error!')
					#await self.send_error(cmd, str(e))
		
			
		except asyncio.CancelledError:
			return
		except Exception as e:
			print('resmon died! %s' % e)
			await out_q.put(NestOpErr(cmd.token, str(e)))

	async def do_gather(self, cmd, out_q, db_url, work_dir, show_progress):
		try:
			progress_queue = asyncio.Queue()
			gatheringmonitor_task = asyncio.create_task(self.__gathermonitor(cmd, progress_queue, out_q))
			
			ldap_url = cmd.ldap_url
			if ldap_url == 'auto':
				if platform.system().lower() == 'windows':
					from winacl.functions.highlevel import get_logon_info
					logon = get_logon_info()
					
					ldap_url = 'ldap+sspi-ntlm://%s\\%s:jackdaw@%s' % (logon['domain'], logon['username'], logon['logonserver'])
			
				else:
					raise Exception('ldap auto mode selected, but it is not supported on this platform')
			
			smb_url = cmd.smb_url
			if smb_url == 'auto':
				if platform.system().lower() == 'windows':
					from winacl.functions.highlevel import get_logon_info
					logon = get_logon_info()
					smb_url = 'smb2+sspi-ntlm://%s\\%s:jackdaw@%s' % (logon['domain'], logon['username'], logon['logonserver'])
			
				else:
					raise Exception('smb auto mode selected, but it is not supported on this platform')
			
			kerberos_url = cmd.kerberos_url					
			dns = cmd.dns
			if dns == 'auto':
				if platform.system().lower() == 'windows':
					from jackdaw.gatherer.rdns.dnstest import get_correct_dns_win
					srv_domain = '%s.%s' % (logon['logonserver'], logon['dnsdomainname'])
					dns = await get_correct_dns_win(srv_domain)
					if dns is None:
						dns = None #failed to get dns
					else:
						dns = str(dns)
			
				else:
					raise Exception('dns auto mode selected, but it is not supported on this platform')
			print(ldap_url)
			print(smb_url)
			print(dns)
			with multiprocessing.Pool() as mp_pool:
				gatherer = Gatherer(
					db_url,
					work_dir,
					ldap_url, 
					smb_url,
					kerb_url=kerberos_url,
					ldap_worker_cnt=int(cmd.ldap_workers), 
					smb_worker_cnt=int(cmd.smb_worker_cnt), 
					mp_pool=mp_pool, 
					smb_gather_types=['all'], 
					progress_queue=progress_queue, 
					show_progress=show_progress,
					calc_edges=True,
					ad_id=None,
					dns=dns,
					stream_data=cmd.stream_data
				)
				res, err = await gatherer.run()
				if err is not None:
					print('gatherer returned error')
					await out_q.put(NestOpErr(cmd.token, str(err)))
					return
				
				#####testing
				await asyncio.sleep(20)
				#######
				
				await out_q.put(NestOpOK(cmd.token))
		except Exception as e:
			logger.exception('do_gather')
			await out_q.put(NestOpErr(cmd.token, str(e)))
		
		finally:
			if gatheringmonitor_task is not None:
				gatheringmonitor_task.cancel()
			progress_queue = None