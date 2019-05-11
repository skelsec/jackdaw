
from jackdaw.dbmodel import *
from jackdaw import logger
from winrecon.cf.c_functions import NetSessionEnum
from winrecon.file_utils import *

from multiprocessing import Process, Queue
from threading import Thread
import threading
from dns import resolver, reversename
import time

class SessMonThread(Thread):
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
				for session in NetSessionEnum(target[:-1]):
					self.outQ.put((target, session))
			except Exception as e:
				logger.debug('SessionMonitor error: %s' % str(e))
				continue
		
class SessMonProc(Process):
	def __init__(self, inQ, outQ, threadcnt):
		Process.__init__(self)
		self.inQ = inQ
		self.outQ = outQ
		self.threadcnt = threadcnt
		self.threads = []
		
	def run(self):
		for i in range(self.threadcnt):
			t = SessMonThread(self.inQ, self.outQ)
			t.daemon = True
			t.start()
			self.threads.append(t)			
		for t in self.threads:
			t.join()
		
class SessMonResProc(Process):
	def __init__(self, outQ, sql_con, dns_server = None):
		Process.__init__(self)
		self.outQ = outQ
		self.rdns_table = {}
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
		
		
	def run(self):
		self.setup()
		while True:
			result = self.outQ.get()
			if not result:
				break
			
			target, session = result
			ip = session.computername.replace('\\\\','')
			
			ns = NetSession()
			ns.source = target
			ns.ip = ip
			ns.rdns = self.rdns_lookup(ip)
			ns.username = session.username
			self.session.add(ns)
			self.session.commit()
			#print('%s: %s\\%s (%s)' % (target, ip, session.username, ns.rdns))
		
class SessionMonitor:
	def __init__(self, db_conn, monitor_time = 60):
		self.db_conn = db_conn
		self.monitor_time = monitor_time
		self.hosts = []
		self.inQ = Queue()
		self.outQ = Queue()
		self.agents = []
		self.result_process = None
		
		self.agent_threadcnt = 4
		self.agent_proccnt = 4
		
	def load_targets_ldap(self, ldap):
		ldap_filter = r'(&(sAMAccountType=805306369))'

		attributes = ['sAMAccountName']
		for entry in ldap.pagedsearch(ldap_filter, attributes):
			self.hosts.append(entry['attributes']['sAMAccountName'])

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
		create_db(self.db_conn)
		
		self.result_process = SessMonResProc(self.outQ, self.db_conn, dns_server = None)
		self.result_process.daemon = True
		self.result_process.start()
		
		for i in range(self.agent_proccnt):
			p = SessMonProc(self.inQ, self.outQ, self.agent_threadcnt)
			p.daemon = True
			p.start()
			self.agents.append(p)
		
		while True:
			#print('=== Polling sessions ===')
			logger.info('=== Polling sessions ===')
			for t in self.hosts:
				self.inQ.put(t)
			if self.monitor_time != -1:
				time.sleep(self.monitor_time)
				break
			
			time.sleep(10)
		
		for a in self.agents:
			for i in range(self.agent_threadcnt):
				self.inQ.put(None)
		
		
		for a in self.agents:
			a.join()
			
		self.outQ.put(None)
		self.result_process.join()
			
		
	