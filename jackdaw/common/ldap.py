import copy
#from msldap.core import *
from msldap.core.common import MSLDAPTargetProxy, MSLDAPCredential, MSLDAPTarget, LDAPProxyType, MSLDAPURLDecoder
from msldap.core.connection import MSLDAPConnection
from jackdaw.common.proxy import ProxyConnection, ProxyType



class LDAPConnectionManager:
	def __init__(self, ldap_connection_string, proxy_connection_string = None):
		self.ldap_connection_string = ldap_connection_string
		self.proxy_connection_string = proxy_connection_string
		
		self.auth = None
		self.target = None
		self.proxy = None

		self.connection = None
		self.ldapurl = MSLDAPURLDecoder(self.ldap_connection_string)
	
	def get_auth(self):
		if self.auth is None:
			self.auth = self.ldapurl.get_credential() #MSLDAPCredential.from_connection_string(self.ldap_connection_string)
		return copy.deepcopy(self.auth)
		
	def get_target(self):
		if self.target is None:
			self.target = self.ldapurl.get_target()
			#self.target = MSLDAPTarget.from_connection_string(self.ldap_connection_string)
			#if self.proxy_connection_string is not None:
			#	lproxy = ProxyConnection.from_connection_string(self.proxy_connection_string)
			#	ldap_proxy = MSLDAPTargetProxy()
			#	ldap_proxy.ip = lproxy.ip
			#	ldap_proxy.port = lproxy.port
			#	ldap_proxy.timeout = lproxy.timeout
			#	ldap_proxy.username = lproxy.username
			#	ldap_proxy.domain = lproxy.domain
			#	ldap_proxy.secret = lproxy.password
			#	ldap_proxy.secret_type = None #TODO? msldap needs to be updated first..
#
			#	if lproxy.type == ProxyType.SOCKS5:
			#		ldap_proxy.proxy_type = LDAPProxyType.SOCKS5
			#	elif lproxy.type == ProxyType.SOCKS5_SSL:
			#		ldap_proxy.proxy_type = LDAPProxyType.SOCKS5_SSL
			#	elif lproxy.type == ProxyType.MULTIPLEXOR:
			#		ldap_proxy.proxy_type = LDAPProxyType.MULTIPLEXOR
			#	elif lproxy.type == ProxyType.MULTIPLEXOR_SSL:
			#		ldap_proxy.proxy_type = LDAPProxyType.MULTIPLEXOR_SSL
			#	
			#	if lproxy.type in [ProxyType.MULTIPLEXOR_SSL, ProxyType.MULTIPLEXOR]:
			#		ldap_proxy.settings = {
			#			'agentid': [lproxy.agentid]
			#		}
#
			#	self.target.proxy = ldap_proxy
			
		return copy.deepcopy(self.target)

	def get_connection(self):
		if self.connection is None:
			self.get_auth()
			self.get_target()
			self.connection = MSLDAPConnection(self.auth, self.target)
			
		return copy.deepcopy(self.connection)
