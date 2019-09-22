import asyncio
import logging
import json
import traceback
import ipaddress
import multiprocessing
import threading

from tqdm import tqdm
from dns import resolver, reversename

import aiosmb
from aiosmb.commons.smbcredential import SMBCredential
from aiosmb.commons.smbtarget import SMBTarget
from aiosmb.commons.smbtargetproxy import SMBTargetProxy
from aiosmb.smbconnection import SMBConnection
from aiosmb.commons.authenticator_builder import AuthenticatorBuilder
from aiosmb.dcerpc.v5.transport.smbtransport import SMBTransport
from aiosmb.dcerpc.v5.interfaces.srvsmgr import SMBSRVS
from aiosmb.dcerpc.v5.interfaces.samrmgr import SMBSAMR
from aiosmb.dcerpc.v5.interfaces.lsatmgr import LSAD

from jackdaw.common.apq import AsyncProcessQueue
from jackdaw.dbmodel.netshare import NetShare
from jackdaw.dbmodel.netsession import NetSession
from jackdaw.dbmodel.localgroup import LocalGroup
from jackdaw import logger
from jackdaw.dbmodel import get_session



class IPHLookup:
	def __init__(self):
		self.dns_server = None
		self.rdns_table = {}
		self.dns_table = {}

	def lookup_dbo(self, dbo):
		"""
		Performs IP and rdns lookup on DB object
		"""
		if dbo.ip is None and dbo.rdns is None:
			logger.warning()
			return dbo

		if dbo.ip is None and dbo.rdns is not None:
			dbo.rdns = self.rdns_lookup(dbo.ip)
			return dbo
		if dbo.ip is not None and dbo.rdns is None:
			dbo.ip = self.rdns_lookup(dbo.rdns)
			return dbo

		return dbo

	def lookup_unknown(self, x):
		"""
		Takes string, decides wether it's and IP address or not, and performs lookup accordingly
		"""
		if x[-1] == '$':
			return (self.ip_lookup(x[:-1]), x[:-1])
		try:
			ipaddress.ip_address(x)
		except:
			return (self.ip_lookup(x), x)
		else:
			return (x, self.rdns_lookup(x))

	def rdns_lookup(self, ip):
		if ip not in self.rdns_table:
			dns_resolver = resolver.Resolver()
			if self.dns_server:
				dns_resolver.nameservers = [self.dns_server]
			try:
				answer = str(dns_resolver.query(reversename.from_address(ip), "PTR")[0])
			except Exception as e:
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


class SMBGathererManager:
	def __init__(self, credential_string, proxy = None):
		self.in_q = AsyncProcessQueue()
		self.out_q = AsyncProcessQueue()
		self.credential_string = credential_string
		self.gathering_type = ['all']
		self.localgroups = ['Administrators', 'Distributed COM Users','Remote Desktop Users']
		self.concurrent_connections = 10
		self.domain = None
		self.dc_ip = None
		self.timeout = 3
		self.db_conn = None

		self.total_targets = 0
		self.targets = []
		self.targets_file = None
		self.ldap_conn = None
		self.out_file = None

		self.gatherer = None
		
		self.use_progress_bar = True
		self.progress_bar = None

		self.results_thread = None
		self.proxy_connection = proxy

	def __target_generator(self):
		for target in self.targets:
			yield target

		if self.targets_file is not None:
			with open(self.targets_file, 'r') as f:
				for line in f:
					line = line.strip()
					yield line

		if self.ldap_conn is not None:
			ldap_filter = r'(&(sAMAccountType=805306369))'
			attributes = ['sAMAccountName']
			for entry in self.ldap_conn.pagedsearch(ldap_filter, attributes):
				yield entry['attributes']['sAMAccountName'][:-1]

	def get_results(self):
		session = None
		if self.db_conn is not None:
			session = get_session(self.db_conn)
		
		while True:
			x = self.out_q.get()
			if x is None:
				break

			target, result, error = x
			if result is not None:
				if session is None:
					logger.debug(target, str(result), error)
				else:
					session.add(result)
					session.commit()

			if result is None and error is None:
				logger.debug('Finished: %s' % target.ip)
				if self.use_progress_bar is True:
					self.progress_bar.update()
	
	def run(self):
		self.in_q = AsyncProcessQueue()
		self.out_q = AsyncProcessQueue()
		if self.use_progress_bar is True:
			self.progress_bar = tqdm()

		self.results_thread = threading.Thread(target = self.get_results)
		self.results_thread.daemon = True
		self.results_thread.start()

		self.credential = SMBCredential.from_credential_string(self.credential_string)
		self.gatherer = AIOSMBGatherer(self.in_q, self.out_q, self.credential, gather = self.gathering_type, localgroups = self.localgroups, concurrent_connections = self.concurrent_connections)
		self.gatherer.start()
		
		if self.proxy_connection:
			proxy = SMBTargetProxy.from_connection_string(self.proxy_connection)
		
		for target in self.__target_generator():
			self.total_targets += 1
			smbt = SMBTarget()
			smbt.ip = target
			#target.hostname = None
			smbt.timeout = self.timeout
			smbt.dc_ip = self.dc_ip
			smbt.domain = self.domain
			if self.proxy_connection:
				smbt.proxy = proxy

			self.in_q.put(smbt)
		
		self.in_q.put(None)
		self.progress_bar.total = self.total_targets

		self.results_thread.join()


class AIOSMBGatherer(multiprocessing.Process):
	def __init__(self, in_q, out_q, credential, gather = ['all'], localgroups = [], concurrent_connections = 10):
		multiprocessing.Process.__init__(self)
		self.in_q = in_q
		self.out_q = out_q
		self.credential = credential
		self.gather = gather
		self.localgroups = localgroups
		self.concurrent_connections = concurrent_connections

		self.targets = []
		self.worker_q = None

	def setup(self):
		pass

	async def scan_host(self, target):
		try:
			spneg = AuthenticatorBuilder.to_spnego_cred(self.credential, target)
			
			async with SMBConnection(spneg, target) as connection:
				results = await asyncio.gather(*[connection.login()], return_exceptions=True)
				if isinstance(results[0], Exception):
					raise results[0]
				if 'all' in self.gather or 'sessions' in self.gather or 'shares' in self.gather:
					async with SMBSRVS(connection) as srvs:
						logger.debug('Connecting to SMBSRVS')
						try:
							await srvs.connect()
						except Exception as e:
							await self.out_q.coro_put((target, None, 'Failed to connect to SMBSRVS. Reason: %s' % e))
						else:
							for level in [10, 1]:
								if 'all' in self.gather or 'sessions' in self.gather:
									try:
										async for username, ip_addr in srvs.list_sessions(level = level):
											sess = NetSession()
											sess.source = target.get_ip()
											sess.ip = ip_addr
											sess.username = username

											await self.out_q.coro_put((target, sess, None))
									except Exception as e:
										if str(e).find('ERROR_INVALID_LEVEL') != -1 and level != 1: #always put there the last level!
											continue
										await self.out_q.coro_put((target, None, 'Failed to get sessions. Reason: %s' % e))

									else:
										break


							if 'all' in self.gather or 'shares' in self.gather:
								try:
									async for name, share_type, remark in srvs.list_shares():
										share = NetShare()
										share.ip = target.get_ip()
										share.netname = name
										share.type = share_type
										share.remark = remark

										await self.out_q.coro_put((target, share, None))

								except:
									tb = traceback.format_exc()
									await self.out_q.coro_put((target, None, 'Failed to list shares. Reason: %s' % tb))

				if 'all' in self.gather or 'localgroups' in self.gather:
					async with LSAD(connection) as lsad:
						logger.debug('Connecting to LSAD')
						try:
							await lsad.connect()
						except Exception as e:
							await self.out_q.coro_put((target, None, 'Failed to connect to LSAD. Reason: %s' % e))
						
						else:
							async with SMBSAMR(connection) as samr:
								logger.debug('Connecting to SAMR')
								try:
									await samr.connect()
								except Exception as e:
									await self.out_q.coro_put((target, None, 'Failed to connect to SAMR. Reason: %s' % e))
								else:
									try:
										policy_handle = await lsad.open_policy2()

										found = False
										try:
											async for domain in samr.list_domains():
												if domain == 'Builtin':
													found = True
													logging.debug('[+] Found Builtin domain')
											
											if found == False:
												raise Exception('[-] Could not find Builtin domain. Fail.')
											#open domain
											domain_sid = await samr.get_domain_sid('Builtin')
											domain_handle = await samr.open_domain(domain_sid)
										except Exception as e:
											tb = traceback.format_exc()
											await self.out_q.coro_put((target, None, 'Failed to list domains. Reason: %s' % tb))
										
										#list aliases
										target_group_rids = {}
										async for name, rid in samr.list_aliases(domain_handle):
											if name in self.localgroups:
												if name not in target_group_rids:
													target_group_rids[name] = []
												target_group_rids[name].append(rid)
										
										if len(target_group_rids) == 0:
											raise Exception('None of the targeted localgroups were found!')
										if len(target_group_rids) != len(self.localgroups):
											logger.debug('Warning! some localgroups were not found!')
										
										for grp in target_group_rids:
											for rid in target_group_rids[grp]:
												#open alias
												alias_handle = await samr.open_alias(domain_handle, rid)
												#list alias memebers
												async for sid in samr.list_alias_members(alias_handle):
													async for domain_name, user_name in lsad.lookup_sids(policy_handle, [sid]):
														lg = LocalGroup()
														lg.ip = target.get_ip()
														lg.hostname = target.get_hostname()
														lg.sid = sid
														lg.groupname = grp
														lg.domain = domain_name
														lg.username = user_name
														await self.out_q.coro_put((target, lg, None))
						
						
						
									except Exception as e:
										tb = traceback.format_exc()
										await self.out_q.coro_put((target, None, 'Failed to connect to poll group memeberships. Reason: %s' % tb))
		
		except Exception as e:
			await self.out_q.coro_put((target, None, 'Failed to connect to host. Reason: %s' % e))
			return

		finally:
			await self.out_q.coro_put((target, None, None)) #target finished

	async def worker(self):
		while True:
			try:
				target = await self.worker_q.get()
				if target is None:
					return
				try:
					await self.scan_host(target)
				except:
					#exception should be handled in scan_host
					continue
			except Exception as e:
				print('WORKER ERROR: %s' % str(e))
				raise

	async def scan_queue(self):
		"""
		Reads targets from queue and scans them
		"""
		self.worker_q = asyncio.Queue()
		tasks = []
		for _ in range(self.concurrent_connections):
			tasks.append(asyncio.create_task(self.worker()))

		while True:
			target = await self.in_q.coro_get()
			if target is None:
				for _ in range(self.concurrent_connections):
					await self.worker_q.put(None)
				break
			else:
				await self.worker_q.put(target)

		results = await asyncio.gather(*tasks, return_exceptions = True)
		for res in results:
			if isinstance(res, Exception):
				logger.error('Error! %s' % res)
		await self.out_q.coro_put(None)
		

	
	def run(self):
		self.setup()
		loop = asyncio.get_event_loop()
		#loop.set_debug(True)  # Enable debug
		loop.run_until_complete(self.scan_queue())


