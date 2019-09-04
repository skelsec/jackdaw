#
#
#
# I am legitimately sorry for this multiprocessing-multithreading bullshit but that's the best one can do in python...

from jackdaw.dbmodel.localgroup import *
from jackdaw.dbmodel import *
from jackdaw import logger

from winrecon.cf.c_functions import NetLocalGroupGetMembers
from winrecon.file_utils import *

from msldap.core.msldap import *
from msldap.ldap_objects import *

from multiprocessing import Process, Queue
from threading import Thread
import threading
from dns import resolver, reversename
import ipaddress


class LocalGroupEnumThread(Thread):
	def __init__(self, inQ, outQ, groups = ['Remote Desktop Users','Administrators','Distributed COM Users']):
		Thread.__init__(self)
		self.groups = groups
		self.inQ = inQ
		self.outQ = outQ
		
	def run(self):
		while True:
			target = self.inQ.get()
			if not target:
				break
			try:
				for groupname in self.groups:
					for group in NetLocalGroupGetMembers(target, groupname, level=2):
						self.outQ.put((target, groupname, group))
			except Exception as e:
				logger.debug('LocalGroupEnumThread error: %s' % str(e))
				continue
		
class LocalGroupEnumProc(Process):
	def __init__(self, inQ, outQ, threadcnt):
		Process.__init__(self)
		self.inQ = inQ
		self.outQ = outQ
		self.threadcnt = threadcnt
		self.threads = []
		
	def run(self):
		for i in range(self.threadcnt):
			t = LocalGroupEnumThread(self.inQ, self.outQ)
			t.daemon = True
			t.start()
			self.threads.append(t)			
		for t in self.threads:
			t.join()
		
class LGResProc(Process):
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
					#print(rdata.address)
					self.dns_table[target] = rdata.address
			except Exception as e:
				logger.debug('LocalGroupEnumThread error: %s' % str(e))
				self.dns_table[target] = None
		return self.dns_table[target]
		
	def run(self):
		self.setup()
		while True:
			result = self.outQ.get()
			if not result:
				break
			
			target, groupname, group = result
			try:
				ip = str(ipaddress.ip_address(target))
			except Exception as e:
				ip = None
			
			if ip is None:
				rdns = target
				ip = self.ip_lookup(target)
			else:
				rdns = self.rdns_lookup(ip)
			
			lg = LocalGroup()
			lg.ip = ip
			lg.rdns = rdns
			lg.sid = str(group.sid)
			lg.sidusage    = group.sidusage
			lg.domain  = group.domain
			lg.username  = group.username
			lg.groupname  = groupname
			if group.domain and group.domain != '':
				lg.hostname  = group.domain.split('.')[0].upper() + '$'
			self.session.add(lg)
			self.session.commit()
			#print('%s %s %s %s %s %s' % (target, ip, rdns, lg.domain, lg.username, lg.sid))
			

class LocalGroupEnumerator:
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

		self.result_process = LGResProc(self.outQ, self.db_con, dns_server = self.dns_server)
		self.result_process.daemon = True
		self.result_process.start()
		
		for _ in range(self.agent_proccnt):
			p = LocalGroupEnumProc(self.inQ, self.outQ, self.agent_threadcnt)
			p.daemon = True
			p.start()
			self.agents.append(p)
		
		logger.info('=== Enumerating local groups ===')
		for t in self.hosts:
			self.inQ.put(t)
		
		for a in self.agents:
			for i in range(self.agent_threadcnt):
				self.inQ.put(None)
			
		for a in self.agents:
			a.join()
		
		self.outQ.put(None)
		self.result_process.join()
		