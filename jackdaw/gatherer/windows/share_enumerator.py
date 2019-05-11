
from jackdaw.dbmodel.netshare import *
from jackdaw.dbmodel import *
from jackdaw import logger

from winrecon.cf.c_functions import NetShareEnum
from winrecon.file_utils import *

from msldap.core.msldap import *
from msldap.ldap_objects import *

from multiprocessing import Process, Queue
from threading import Thread
import threading
from dns import resolver, reversename
import ipaddress


class ShareEnumThread(Thread):
	def __init__(self, inQ, outQ):
		Thread.__init__(self)
		self.inQ = inQ
		self.outQ = outQ
		
	def run(self):
		while True:
			target = self.inQ.get()
			if not target:
				break
			try:
				for share in NetShareEnum(target, level=1):
					self.outQ.put((target, share))
			except Exception as e:
				logger.debug('ShareEnumerator error: %s' % str(e))
				continue
		
class ShareEnumProc(Process):
	def __init__(self, inQ, outQ, threadcnt):
		Process.__init__(self)
		self.inQ = inQ
		self.outQ = outQ
		self.threadcnt = threadcnt
		self.threads = []
		
	def run(self):
		for i in range(self.threadcnt):
			t = ShareEnumThread(self.inQ, self.outQ)
			t.daemon = True
			t.start()
			self.threads.append(t)			
		for t in self.threads:
			t.join()
		
class SMResProc(Process):
	def __init__(self, outQ, sql_con, dns_server = None):
		Process.__init__(self)
		self.outQ = outQ
		self.rdns_table = {}
		self.dns_table = {}
		self.session = None
		self.conn = sql_con
		self.dns_server = dns_server
		
	def setup(self):
		self.session = get_session(self.conn)
	
	def rdns_lookup(self, ip):
		if ip not in self.rdns_table:
			dns_resolver = resolver.Resolver()
			if self.dns_server:
				dns_resolver.nameservers = [self.dns_server]
			try:
				answer = str(dns_resolver.query(reversename.from_address(ip), "PTR")[0])
			except Exception as e:
				#print(e)
				answer = 'NA'
				pass
				
			self.rdns_table[ip] = answer
		return self.rdns_table[ip]
		
	def ip_lookup(self, target):
		if target not in self.dns_table:
			dns_resolver = resolver.Resolver()
			if self.dns_server:
				dns_resolver.nameservers = [self.dns_server]
			try:
				answers = dns_resolver.query(target, 'A')
				for rdata in answers:
					self.dns_table[target] = rdata.address
			except Exception as e:
				logger.debug('ShareEnumerator error: %s' % str(e))
				self.dns_table[target] = None
		return self.dns_table[target]
		
	def run(self):
		self.setup()
		while True:
			result = self.outQ.get()
			if not result:
				break
			
			target, share = result
			try:
				ip = str(ipaddress.ip_address(target))
			except Exception as e:
				#print(e)
				ip = None
			
			if ip is None:
				rdns = target
				ip = self.ip_lookup(target)
			else:
				rdns = self.rdns_lookup(ip)
			
			ns = NetShare()
			ns.ip = ip
			ns.rdns = rdns
			ns.netname = share.netname
			ns.type    = share.type
			ns.remark  = share.remark
			ns.passwd  = share.passwd
			self.session.add(ns)
			self.session.commit()
			#print('%s %s %s %s' % (target, ip, rdns, ns.netname))
			

class ShareEnumerator:
	def __init__(self, db_con, dns_server = None):
		self.db_con = db_con
		self.hosts = []
		self.inQ = Queue()
		self.outQ = Queue()
		self.agents = []
		self.result_process = None
		self.dns_server = dns_server
		
		self.agent_proccnt = 4
		self.agent_threadcnt = 4
		
		
	def load_targets_ldap(self, ldap):
		ldap_filter = r'(&(sAMAccountType=805306369))'

		attributes = ['sAMAccountName']
		for entry in ldap.pagedsearch(ldap_filter, attributes):
			self.hosts.append(entry['attributes']['sAMAccountName'][:-1])
			
	def load_targets_file(self, filename):
		with open(filename,'r') as f:
			for line in f:
				line=line.strip()
				if line == '':
					continue
				self.hosts.append(line)
				
	def load_tagets(self, targets):
		self.hosts = targets
		
	def run(self):
		create_db(self.db_con)

		self.result_process = SMResProc(self.outQ, self.db_con, dns_server = self.dns_server)
		self.result_process.daemon = True
		self.result_process.start()
		
		for i in range(self.agent_proccnt):
			p = ShareEnumProc(self.inQ, self.outQ, self.agent_threadcnt)
			p.daemon = True
			p.start()
			self.agents.append(p)
		
		logger.info('=== Enumerating shares ===')
		for t in self.hosts:
			self.inQ.put(t)
		
		for a in self.agents:
			for i in range(self.agent_threadcnt):
				self.inQ.put(None)
			
		for a in self.agents:
			a.join()
		
		self.outQ.put(None)
		self.result_process.join()
		