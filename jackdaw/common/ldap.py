import copy
#from msldap.core import *
from msldap.core.common import MSLDAPTargetProxy, MSLDAPCredential, MSLDAPTarget, LDAPProxyType, MSLDAPURLDecoder
from msldap.core.connection import MSLDAPConnection
from jackdaw.common.proxy import ProxyConnection, ProxyType
from jackdaw import logger


class LDAPConnectionManager:
	def __init__(self, ldap_connection_string):
		self.ldap_connection_string = ldap_connection_string
		
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
		return copy.deepcopy(self.target)

	def get_connection(self):
		if self.connection is None:
			self.get_auth()
			self.get_target()
			logger.debug(self.get_target())
			self.connection = MSLDAPConnection(self.auth, self.target)
			
		return copy.deepcopy(self.connection)
