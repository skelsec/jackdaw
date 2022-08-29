from . import Basemodel
import ipaddress
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, exc
from jackdaw.dbmodel.utils.serializer import Serializer
import hashlib

class CustomTarget(Basemodel, Serializer):
	__tablename__ = 'customtargets'
	
	id = Column(Integer, primary_key=True)
	ownerid = Column(String, index=True)
	linksid = Column(String, index=True)
	hostname = Column(String, index=True)
	description = Column(String, index=True)
	checksum = Column(String, index=True)

	def __init__(self, hostname, description, linksid = None, ownerid=None):
		self.linksid = linksid
		self.hostname = hostname
		self.ownerid = ownerid
		self.description = description
		self.checksum = CustomTarget.calc_checksum(self.hostname, self.description, self.linksid, self.ownerid)


	@staticmethod
	def calc_checksum(hostname, description, linksid, ownerid):
		buff = str(hostname) + str(description) + str(linksid) + str(description) + str(ownerid)
		return hashlib.md5(buff.encode()).hexdigest()
	
#	def get_smb_target(self, domain = None, proxy = None, dc_ip = None, timeout = 1):
#		ip = None
#		hostname = self.hostname
#		try:
#			ipaddress.ip_address(hostname)
#			ip = hostname
#			hostname = None
#		except:
#			pass
#		print('get_smb_target: domain: %s , ip: %s, hostname: %s' % (domain, ip, hostname))
#		return SMBTarget(
#			ip = ip,
#			hostname = hostname, 
#			timeout = timeout,
#			dc_ip = dc_ip, 
#			domain = domain, 
#			proxy = proxy,
#			protocol = SMBConnectionProtocol.TCP,
#			path = None
#		)
#	
#	def get_rdp_target(self, domain = None, proxy = None, dc_ip = None, timeout = 1):
#		from aardwolf.commons.target import RDPTarget
#
#		ip = None
#		hostname = self.hostname
#		try:
#			ipaddress.ip_address(hostname)
#			ip = hostname
#			hostname = None
#		except:
#			pass
#		
#		print('get_rdp_target: domain: %s , ip: %s, hostname: %s' % (domain, ip, hostname))
#		return RDPTarget(
#			ip = ip,
#			hostname = hostname,
#			dc_ip = dc_ip,
#			domain = domain,
#			proxy = proxy
#		)
#		
#	def get_ldap_target(self, proxy = None, timeout = 1):
#		return MSLDAPTarget(
#			self.hostname, 
#			#port = 389, 
#			#proto = LDAPProtocol.TCP, 
#			#tree = None, 
#			proxy = proxy, 
#			timeout = timeout, 
#			#ldap_query_page_size = 1000, 
#			#ldap_query_ratelimit = 0
#		)
#	
#	def get_kerberos_target(self, proxy = None, timeout = 1):
#		kt = KerberosTarget()
#		kt.ip = self.hostname
#		kt.port = 88
#		kt.protocol = KerberosSocketType.TCP
#		kt.proxy = proxy
#		kt.timeout = timeout
#		return kt
#