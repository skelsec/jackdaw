import copy
import enum
from urllib.parse import urlparse, parse_qs

from jackdaw.common.proxy import ProxyConnection, ProxyType

from aiosmb.commons.smbcredential import SMBCredential, SMBCredentialsSecretType, SMBCredentialsAuthType
from aiosmb.commons.smbtargetproxy import SMBTargetProxy, SMBTargetProxySecretType, SMBTargetProxyServerType
from aiosmb.commons.smbtarget import SMBTarget

class SMBAuthType(enum.Enum):
	NTLM = 'NTLM'
	KERBEROS = 'KERBEROS'
	SSPI_NTLM = 'SSPI_NTLM'
	SSPI_KERBEROS = 'SSPI_KERBEROS'
	ANONYMOUS = 'ANONYMOUS'
	SSPI = 'SSPI'
	MULTIPLEXOR = 'MULTIPLEXOR'
	MULTIPLEXOR_SSL = 'MULTIPLEXOR_SSL'

class SMBSecretType(enum.Enum):
	NT = 'NT'
	PASSWORD = 'PASSWORD'
	AES = 'AES'
	RC4 = 'RC4'
	CCACHE = 'CCACHE'
	NONE = 'NONE'

class SMBAuth:
	"""
	kerberos-password://domain\\user:pass@doesntmatter
	"""
	def __init__(self):
		self.type = None
		self.username = None
		self.secret = None
		self.secret_type = None
		self.domain = None

	@staticmethod
	def from_credential_string(s):
		url_e = urlparse(s)
		atype_raw = url_e.scheme.split('-')
		atype = SMBAuthType(atype_raw[0].upper())
		if atype == SMBAuthType.NTLM:
			auth = SMBNTLMAuth()
		elif atype == SMBAuthType.KERBEROS:
			auth = SMBKerberosAuth()
		elif atype == SMBAuthType.ANONYMOUS:
			auth = SMBAnonymousAuth()
		elif atype == SMBAuthType.SSPI:
			auth = SMBSSPIAuth()
		elif atype in [SMBAuthType.MULTIPLEXOR, SMBAuthType.MULTIPLEXOR_SSL]:
			auth = SMBMultiplexorAuth()

		auth.type = atype
		
		if len(atype_raw) == 2:
			auth.secret_type = SMBSecretType(atype_raw[1].upper())
		else:
			if auth.type in [SMBAuthType.NTLM, SMBAuthType.KERBEROS]:
				raise Exception('Secret type must be defined!')
			elif atype in [SMBAuthType.ANONYMOUS, SMBAuthType.MULTIPLEXOR, SMBAuthType.MULTIPLEXOR_SSL]:
				auth.secret_type = SMBSecretType.NONE
			elif atype == SMBAuthType.SSPI:
				auth.secret_type = SMBSecretType.PASSWORD
				auth.username = '<CURRENT>'
				auth.secret = '<CURRENT>'
				auth.domain = '<CURRENT>'
		
		auth.secret = url_e.password
		if url_e.username is not None:
			if url_e.username.find('\\') != -1:
				auth.domain, auth.username = url_e.username.split('\\')
			else:
				auth.username = url_e.username
		
		auth.parse_rest(url_e)

		return auth

class SMBAnonymousAuth(SMBAuth):
	def __init__(self):
		SMBAuth.__init__(self)

	def parse_rest(self, url_e):
		return

class SMBNTLMAuth(SMBAuth):
	def __init__(self):
		SMBAuth.__init__(self)

	def parse_rest(self, url_e):
		return

class SMBKerberosAuth(SMBAuth):
	def __init__(self):
		SMBAuth.__init__(self)

	def parse_rest(self, url_e):
		return

class SMBSSPIAuth(SMBAuth):
	def __init__(self):
		SMBAuth.__init__(self)

	def parse_rest(self, url_e):
		return

class SMBMultiplexorAuth(SMBAuth):
	def __init__(self):
		SMBAuth.__init__(self)

	def parse_rest(self, url_e):
		self.agentid = url_e.path.replace('/','')
		if self.agentid is None:
			raise Exception('Multiplexor proxy requires agentid to be set!')

		return


class SMBConnectionManager:
	def __init__(self, credential_string, proxy_connection_string = None):
		self.credential_string = credential_string
		self.proxy_connection_string = proxy_connection_string
		
		self.auth = None
		self.target = None
		self.proxy = None

		self.connection = None
	
	def get_auth(self):
		if self.auth is None:
			auth = SMBAuth.from_credential_string(self.credential_string)
			if auth.type == SMBAuthType.NTLM:
				atype = SMBCredentialsAuthType.NTLM
			elif auth.type == SMBAuthType.KERBEROS:
				atype = SMBCredentialsAuthType.KERBEROS
			elif auth.type == SMBAuthType.SSPI_KERBEROS:
				atype = SMBCredentialsAuthType.SSPI_KERBEROS
			elif auth.type == SMBAuthType.SSPI_NTLM:
				atype = SMBCredentialsAuthType.SSPI_NTLM
			elif auth.type == SMBAuthType.MULTIPLEXOR:
				atype = SMBCredentialsAuthType.MULTIPLEXOR
			elif auth.type == SMBAuthType.MULTIPLEXOR_SSL:
				atype = SMBCredentialsAuthType.MULTIPLEXOR_SSL

			if auth.secret_type == SMBSecretType.NT:
				stype = SMBCredentialsSecretType.NT
			elif auth.secret_type == SMBSecretType.PASSWORD:
				stype = SMBCredentialsSecretType.PASSWORD
			elif auth.secret_type == SMBSecretType.AES:
				stype = SMBCredentialsSecretType.AES
			elif auth.secret_type == SMBSecretType.RC4:
				stype = SMBCredentialsSecretType.RC4
			elif auth.secret_type == SMBSecretType.CCACHE:
				stype = SMBCredentialsSecretType.CCACHE
			elif auth.secret_type == SMBSecretType.NONE:
				stype = SMBCredentialsSecretType.NONE

			
			settings = None
			if auth.type in [SMBAuthType.MULTIPLEXOR, SMBAuthType.MULTIPLEXOR_SSL]:
				settings = {
					'agentid': [auth.agentid]
				}

			self.auth = SMBCredential(
				username = self.auth.username, 
				domain = self.auth.domain, 
				secret = self.auth.secret, 
				secret_type = stype, 
				authentication_type = atype, 
				settings = settings
			)
		return copy.deepcopy(self.auth)
		
	def get_connection_from_taget(self, ip, timeout = 3, dc_ip = None):   #, hostname = None):
		if self.proxy is None and self.proxy_connection_string is not None:
			proxy = ProxyConnection.from_connection_string(self.proxy_connection_string)
			if proxy.type == ProxyType.SOCKS5:
				pytpe = SMBTargetProxyServerType.SOCKS5
			elif proxy.type == ProxyType.SOCKS5_SSL:
				pytpe = SMBTargetProxyServerType.SOCKS5_SSL
			elif proxy.type == ProxyType.MULTIPLEXOR:
				pytpe = SMBTargetProxyServerType.MULTIPLEXOR
			elif proxy.type == ProxyType.MULTIPLEXOR_SSL:
				pytpe = SMBTargetProxyServerType.MULTIPLEXOR_SSL
			
			agent_id = None
			stype = SMBTargetProxySecretType.NONE
			if proxy.type in [ProxyType.SOCKS5, ProxyType.SOCKS5_SSL]:
				if proxy.username is not None:
					stype = SMBTargetProxySecretType.PLAIN
			elif proxy.type in [ProxyType.MULTIPLEXOR, ProxyType.MULTIPLEXOR_SSL]:
				if proxy.username is not None:
					stype = SMBTargetProxySecretType.PLAIN
				agent_id = proxy.agentid
			
			
			self.proxy = SMBTargetProxy(
				ip = proxy.ip,
				port = proxy.port,
				timeout = proxy.timeout,
				proxy_type = pytpe,
				username = proxy.username,
				domain = proxy.domain,
				secret = proxy.password,
				secret_type = stype,
				agent_id = agent_id
			)

		smbt = SMBTarget()
		smbt.ip = ip
		#target.hostname = None
		smbt.timeout = timeout
		smbt.dc_ip = dc_ip
		smbt.domain = self.auth.domain
		if self.proxy:
			smbt.proxy = copy.deepcopy(self.proxy)

		return smbt 
		
