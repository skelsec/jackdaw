import copy
#from msldap.core import *
from msldap.commons.factory import LDAPConnectionFactory

from msldap.core.connection import MSLDAPConnection
from jackdaw.common.proxy import ProxyConnection, ProxyType
from jackdaw import logger


class LDAPConnectionManager:
	def __init__(self, ldap_connection_string):
		self.ldap_connection_string = ldap_connection_string
		
		self.auth = None
		self.target = None

		self.connection = None
		self.ldapurl = LDAPConnectionFactory.from_url(self.ldap_connection_string)

	def get_connection(self):			
		return self.ldapurl.get_connection()
