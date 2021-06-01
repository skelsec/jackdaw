import asyncio
import multiprocessing
import platform
import datetime
import traceback

from jackdaw.dbmodel.adinfo import ADInfo
from jackdaw.dbmodel.edgelookup import EdgeLookup
from jackdaw.dbmodel.aduser import ADUser
from jackdaw.dbmodel.adgroup import Group
from jackdaw.dbmodel.adcomp import Machine

from jackdaw.dbmodel.netshare import NetShare
from jackdaw.dbmodel.netsession import NetSession
from jackdaw.dbmodel.localgroup import LocalGroup
from jackdaw.dbmodel.edge import Edge
from jackdaw.dbmodel.edgelookup import EdgeLookup
from jackdaw.dbmodel.customtarget import CustomTarget
from jackdaw.dbmodel.storedcreds import StoredCred
from jackdaw.dbmodel.graphinfo import GraphInfoAD, GraphInfo



from jackdaw.dbmodel import create_db, get_session, windowed_query

from jackdaw.gatherer.gatherer import Gatherer
from jackdaw.gatherer.scanner.scanner import *
from jackdaw.nest.ws.protocol import *

from jackdaw.nest.graph.graphdata import GraphData
from jackdaw import logger
from jackdaw.gatherer.progress import GathererProgressType

#testing
import random

STANDARD_PROGRESS_MSG_TYPES = [
	GathererProgressType.BASIC,  
	GathererProgressType.SD,
	GathererProgressType.SDUPLOAD,
	GathererProgressType.MEMBERS,
	GathererProgressType.MEMBERSUPLOAD,
	GathererProgressType.SMB,
	GathererProgressType.KERBEROAST,
	GathererProgressType.SDCALC,
	GathererProgressType.SDCALCUPLOAD,
	GathererProgressType.INFO,
]

class NestOperator:
	def __init__(self, websocket, db_url, work_dir, graph_type):
		self.websocket = websocket
		self.db_url = db_url
		self.db_session = None
		self.work_dir = work_dir
		self.ad_id = None
		self.show_progress = True #prints progress to console?
		self.graphs = {}
		self.graph_type = graph_type
		self.graph_id = None
		self.edgeinfo_cache = {}

		# for intercom ops
		self.intercom_q_in = None #intercom_q_in
		self.intercom_q_out = None #intercom_q_out
		self.operatorid = None

	async def __handle_intercom_in(self):
		while True:
			packet = await self.intercom_q_in.get()
			print(packet)


	def loadgraph(self, graphid):
		graphid = int(graphid)
		graph_cache_dir = self.work_dir.joinpath('graphcache')
		graph_dir = graph_cache_dir.joinpath(str(graphid))
		if graph_dir.exists() is False:
			raise Exception('Graph cache dir doesnt exists!')
		else:
			self.graphs[graphid] = self.graph_type.load(self.db_session, graphid, graph_dir)
		
		return True


	def lookup_oid(self, oint, ad_id, token):
		try:
			if oint not in self.edgeinfo_cache:
				edgeinfo = self.db_session.query(EdgeLookup).get(oint)
				self.edgeinfo_cache[oint] = edgeinfo.oid

			return self.edgeinfo_cache[oint] 
		except Exception as e:
			logger.exception('lookup_oid')

	async def do_listgraphs(self, cmd):
		gr = NestOpListGraphRes()
		gr.token = cmd.token
		
		for res in self.db_session.query(GraphInfo).all():	
			gr.gids.append(res.id)
		
		await self.websocket.send(gr.to_json())
		await self.send_ok(cmd)

	async def do_changegraph(self, cmd):
		if cmd.graphid not in self.listgraphs():
			await self.send_error(cmd, 'Graph id not found')

		self.graph_id = int(cmd.graphid)
		await self.send_ok(cmd)

	async def send_error(self, ocmd, reason = None):
		reply = NestOpErr()
		reply.token = ocmd.token
		reply.reason = reason
		await self.websocket.send(reply.to_json())
	
	async def send_ok(self, ocmd):
		reply = NestOpOK()
		reply.token = ocmd.token
		await self.websocket.send(reply.to_json())

	async def send_reply(self, ocmd, reply):
		reply.token = ocmd.token
		await self.websocket.send(reply.to_json())
	
	async def spam_sessions(self, temp_tok_testing, temp_adid_testing, machine_sids_testing, usernames_testing):
		###### TESTING!!!!! DELETE THIS!!!!
		logger.info('SPEM!!!!!!!!!!!!!!!!!!!!!!!!!!!!!1')
		for _ in range(1000):
			await asyncio.sleep(0.01)
			reply = NestOpSMBSessionRes()
			reply.token = temp_tok_testing
			reply.adid = temp_adid_testing
			reply.machinesid = random.choice(machine_sids_testing)
			reply.username = random.choice(usernames_testing)
			await self.websocket.send(reply.to_json())
				
	async def __gathermonitor(self, cmd, results_queue):
		try:
			usernames_testing = []
			machine_sids_testing = []
			
			temp_tok_testing = None
			temp_adid_testing = None
			temp_started = False
			
			while True:
				try:
					msg = await results_queue.get()
					if msg is None:
						break
					
					#print(msg)
					if msg.type in STANDARD_PROGRESS_MSG_TYPES:
						##### TESTING
						temp_tok_testing = cmd.token
						temp_adid_testing = msg.adid
						
						######
						reply = NestOpGatherStatus()
						reply.token = cmd.token
						reply.current_progress_type = msg.type.value
						reply.msg_type = msg.msg_type.value
						reply.adid = msg.adid
						reply.domain_name = msg.domain_name
						reply.total = msg.total
						reply.step_size = msg.step_size
						reply.basic_running = []
						if msg.running is not None:
							reply.basic_running = [x for x in msg.running]
						reply.basic_finished = msg.finished
						reply.smb_errors = msg.errors
						reply.smb_sessions = msg.sessions
						reply.smb_shares = msg.shares
						reply.smb_groups = msg.groups
						await self.websocket.send(reply.to_json())
						
						####TESTINGTESTING!!!!
						if msg.type.value != 'LDAP_BASIC':
							if temp_started is False:
								asyncio.create_task(self.spam_sessions(temp_tok_testing, temp_adid_testing, machine_sids_testing, usernames_testing))
								temp_started = True
								
					elif msg.type == GathererProgressType.USER:
						usernames_testing.append(msg.data.sAMAccountName)
						reply = NestOpUserRes()
						reply.token = cmd.token
						reply.name = msg.data.sAMAccountName
						reply.adid = msg.data.ad_id
						reply.sid = msg.data.objectSid
						reply.kerberoast = 1 if msg.data.servicePrincipalName is not None else 0
						reply.asreproast = int(msg.data.UAC_DONT_REQUIRE_PREAUTH)
						reply.nopassw = int(msg.data.UAC_PASSWD_NOTREQD)
						reply.cleartext = int(msg.data.UAC_ENCRYPTED_TEXT_PASSWORD_ALLOWED)
						reply.smartcard = int(msg.data.UAC_SMARTCARD_REQUIRED)
						reply.active = int(msg.data.canLogon)
						reply.description = msg.data.description
						reply.is_admin = int(msg.data.adminCout)

						await self.websocket.send(reply.to_json())
					
					elif msg.type == GathererProgressType.MACHINE:
						machine_sids_testing.append(msg.data.objectSid)
						reply = NestOpComputerRes()
						reply.token = cmd.token
						reply.name = msg.data.sAMAccountName
						reply.adid = msg.data.ad_id
						reply.sid = msg.data.objectSid
						reply.domainname = msg.data.dNSHostName
						reply.osver = msg.data.operatingSystem
						reply.ostype = msg.data.operatingSystemVersion
						reply.description = msg.data.description
						if msg.data.UAC_SERVER_TRUST_ACCOUNT is True:
							reply.computertype = 'DOMAIN_CONTROLLER'
						elif msg.data.operatingSystem is not None:
							if msg.data.operatingSystem.lower().find('windows') != -1:
								if msg.data.operatingSystem.lower().find('server') != -1:
									reply.computertype = 'SERVER'
								else:
									reply.computertype = 'WORKSTATION'
							else:
								reply.computertype = 'NIX'
						else:
							reply.computertype = 'DUNNO'
						

						await self.websocket.send(reply.to_json())
					
					elif msg.type == GathererProgressType.SMBLOCALGROUP:
						reply = NestOpSMBLocalGroupRes()
						reply.token = cmd.token
						reply.adid = msg.data.ad_id
						reply.machinesid = msg.data.machine_sid
						reply.usersid = msg.data.sid
						reply.groupname = msg.data.groupname
						await self.websocket.send(reply.to_json())
					
					elif msg.type == GathererProgressType.SMBSHARE:
						reply = NestOpSMBShareRes()
						reply.token = cmd.token
						reply.adid = msg.data.ad_id
						reply.machinesid = msg.data.machine_sid
						reply.netname = msg.data.netname
						await self.websocket.send(reply.to_json())
					
					elif msg.type == GathererProgressType.SMBSESSION:					
						reply = NestOpSMBSessionRes()
						reply.token = cmd.token
						reply.adid = msg.data.ad_id
						reply.machinesid = msg.data.machine_sid
						reply.username = msg.data.username
						await self.websocket.send(reply.to_json())
					
					elif msg.type == GathererProgressType.GROUP:					
						reply = NestOpGroupRes()
						reply.token = cmd.token
						reply.adid = msg.data.ad_id
						reply.name = msg.data.sAMAccountName
						reply.dn = msg.data.dn
						reply.guid = msg.data.objectGUID
						reply.sid = msg.data.objectSid
						reply.description = msg.data.description
						await self.websocket.send(reply.to_json())
						
				except asyncio.CancelledError:
					return
				except Exception as e:
					logger.exception('resmon processing error!')
					#await self.send_error(cmd, str(e))
		
			
		except asyncio.CancelledError:
			return
		except Exception as e:
			print('resmon died! %s' % e)
			await self.send_error(cmd, str(e))
	

	async def do_gather(self, cmd):
		try:
			progress_queue = asyncio.Queue()
			gatheringmonitor_task = asyncio.create_task(self.__gathermonitor(cmd, progress_queue))
			
			ldap_url = cmd.ldap_url
			if ldap_url == 'auto':
				if platform.system().lower() == 'windows':
					from winacl.functions.highlevel import get_logon_info
					logon = get_logon_info()
					
					ldap_url = 'ldap+sspi-ntlm://%s\\%s:jackdaw@%s' % (logon['domain'], logon['username'], logon['logonserver'])
			
				else:
					raise Exception('ldap auto mode selected, but it is not supported on this platform')
			
			smb_url = cmd.smb_url
			if smb_url == 'auto':
				if platform.system().lower() == 'windows':
					from winacl.functions.highlevel import get_logon_info
					logon = get_logon_info()
					smb_url = 'smb2+sspi-ntlm://%s\\%s:jackdaw@%s' % (logon['domain'], logon['username'], logon['logonserver'])
			
				else:
					raise Exception('smb auto mode selected, but it is not supported on this platform')
			
			kerberos_url = cmd.kerberos_url					
			dns = cmd.dns
			if dns == 'auto':
				if platform.system().lower() == 'windows':
					from jackdaw.gatherer.rdns.dnstest import get_correct_dns_win
					srv_domain = '%s.%s' % (logon['logonserver'], logon['dnsdomainname'])
					dns = await get_correct_dns_win(srv_domain)
					if dns is None:
						dns = None #failed to get dns
					else:
						dns = str(dns)
			
				else:
					raise Exception('dns auto mode selected, but it is not supported on this platform')
			print(ldap_url)
			print(smb_url)
			print(dns)
			with multiprocessing.Pool() as mp_pool:
				gatherer = Gatherer(
					self.db_url,
					self.work_dir,
					ldap_url, 
					smb_url,
					kerb_url=kerberos_url,
					ldap_worker_cnt=int(cmd.ldap_workers), 
					smb_worker_cnt=int(cmd.smb_worker_cnt), 
					mp_pool=mp_pool, 
					smb_gather_types=['all'], 
					progress_queue=progress_queue, 
					show_progress=self.show_progress,
					calc_edges=True,
					ad_id=None,
					dns=dns,
					stream_data=cmd.stream_data
				)
				res, err = await gatherer.run()
				if err is not None:
					print('gatherer returned error')
					await self.send_error(cmd, str(err))
					return
				
				#####testing
				await asyncio.sleep(20)
				#######
				
				await self.send_ok(cmd)
		except Exception as e:
			logger.exception('do_gather')
			await self.send_error(cmd, str(e))
		
		finally:
			if gatheringmonitor_task is not None:
				gatheringmonitor_task.cancel()
			progress_queue = None
	
	async def do_listads(self, cmd):
		"""
		Lists all available adid in the DB
		Sends back a NestOpListADRes reply or ERR in case of failure
		"""
		try:
			reply = NestOpListADRes()
			for i in self.db_session.query(ADInfo.id).all():
				reply.adids.append(i[0])
			
			await self.send_reply(cmd, reply)
			await self.send_ok(cmd)
		except Exception as e:
			logger.exception('do_listads')
			await self.send_error(cmd, e)
	
	async def do_changead(self, cmd):
		"""
		Changes the current AD to another, specified by ad_id in the command.
		Doesnt have a dedicated reply, OK means change is succsess, ERR means its not
		"""
		try:
			res = self.db_session.query(ADInfo).get(cmd.adid)
			print(res)
			if res is None:
				await self.send_error(cmd, 'No such AD in database')
				return
			
			self.ad_id = res.id
			await self.send_ok(cmd)
		except Exception as e:
			logger.exception('do_listads')
			await self.send_error(cmd, e)

	async def do_getobjinfo(self, cmd):
		res = self.db_session.query(EdgeLookup).filter_by(oid = cmd.oid).filter(EdgeLookup.ad_id == self.ad_id).first()
		if res is None:
			await self.send_error(cmd, 'No object found with that OID')
			return

		if res.otype == 'user':
			obj = self.db_session.query(ADUser).filter_by(objectSid = res.oid).filter(ADUser.ad_id == self.ad_id).first()
			if obj is None:
				await self.send_error(cmd, 'Not find in destination DB')
				return

			await self.send_result(cmd, obj)

	async def do_load_graph(self, cmd):
		try:
			# loads an AD scan and sends all results to the client
			logger.info('do_load_graph')
			# sanity check if the AD exists
			qry_res = self.db_session.query(GraphInfoAD.ad_id).filter_by(graph_id = cmd.graphid).all()
			if qry_res is None:
				await self.send_error(cmd, 'No AD ID exists with that ID')
				return
			res = []
			for r in qry_res:
				res.append(r[0]) #ugly, pls fix!

			#logger.info('res %s' % res)
			for adid in res:
				#sending machines
				logger.info('computer!')
				compbuff = NestOpComputerBuffRes()
				compbuff.token = cmd.token
				qry = self.db_session.query(Machine).filter_by(ad_id = adid)
				for computer  in windowed_query(qry, Machine.id, 100):
					await asyncio.sleep(0)
					reply = NestOpComputerRes()
					reply.token = cmd.token
					reply.name = computer.sAMAccountName
					reply.adid = computer.ad_id
					reply.sid = computer.objectSid
					reply.domainname = computer.dNSHostName
					reply.osver = computer.operatingSystem
					reply.ostype = computer.operatingSystemVersion
					reply.description = computer.description
					if computer.isAdmin is not None:
						reply.is_admin = int(computer.isAdmin)
					reply.isinactive = 1
					if computer.lastLogonTimestamp is not None:
						if (datetime.datetime.utcnow() - computer.lastLogonTimestamp).days > (6 * 30):
							reply.isinactive = 0
					
					if computer.UAC_SERVER_TRUST_ACCOUNT is True:
						reply.computertype = 'DOMAIN_CONTROLLER'
					elif computer.operatingSystem is not None:
						if computer.operatingSystem.lower().find('windows') != -1:
							if computer.operatingSystem.lower().find('server') != -1:
								reply.computertype = 'SERVER'
							else:
								reply.computertype = 'WORKSTATION'
						else:
							reply.computertype = 'NIX'
					else:
						reply.computertype = 'DUNNO'
							

					compbuff.computers.append(reply)
					if len(compbuff.computers) >= 100:
						await self.websocket.send(compbuff.to_json())
						compbuff = NestOpComputerBuffRes()
						compbuff.token = cmd.token

				if len(compbuff.computers) > 0:
					await self.websocket.send(compbuff.to_json())
					compbuff = NestOpComputerBuffRes()
					compbuff.token = cmd.token


			for adid in res:
				#sending users
				logger.info('users!')
				userbuff = NestOpUserBuffRes()
				userbuff.token = cmd.token
				qry = self.db_session.query(ADUser).filter_by(ad_id = adid)
				for user in windowed_query(qry, ADUser.id, 100):
					await asyncio.sleep(0)
					reply = NestOpUserRes()
					reply.token = cmd.token
					reply.name = user.sAMAccountName
					reply.adid = user.ad_id
					reply.sid = user.objectSid
					reply.kerberoast = 1 if user.servicePrincipalName is not None else 0
					reply.asreproast = int(user.UAC_DONT_REQUIRE_PREAUTH)
					reply.nopassw = int(user.UAC_PASSWD_NOTREQD)
					reply.cleartext = int(user.UAC_ENCRYPTED_TEXT_PASSWORD_ALLOWED)
					reply.smartcard = int(user.UAC_SMARTCARD_REQUIRED)
					reply.active = int(user.canLogon)
					reply.description = user.description
					if user.adminCount is not None:
						reply.is_admin = int(user.adminCount)
					else:
						reply.is_admin = 0
					userbuff.users.append(reply)
					if len(userbuff.users) >= 100:
						await self.websocket.send(userbuff.to_json())
						userbuff = NestOpUserBuffRes()
						userbuff.token = cmd.token

				if len(userbuff.users) > 0:
					await self.websocket.send(userbuff.to_json())
					userbuff = NestOpUserBuffRes()
					userbuff.token = cmd.token
			
			for adid in res:
				#sending localgroups
				logger.info('localgroups!')
				for lgroup in self.db_session.query(LocalGroup).filter_by(ad_id = adid).all():
					await asyncio.sleep(0)
					reply = NestOpSMBLocalGroupRes()
					reply.token = cmd.token
					reply.adid = lgroup.ad_id
					reply.machinesid = lgroup.machine_sid
					reply.usersid = lgroup.sid
					reply.groupname = lgroup.groupname
					await self.websocket.send(reply.to_json())
			
			for adid in res:
				#sending smb shares
				logger.info('SHARES!')
				sharebuffer = NestOpSMBShareBuffRes()
				sharebuffer.token = cmd.token
				qry = self.db_session.query(NetShare).filter_by(ad_id = adid)
				for share in windowed_query(qry, NetShare.id, 100):
					await asyncio.sleep(0)
					reply = NestOpSMBShareRes()
					reply.token = cmd.token
					reply.adid = share.ad_id
					reply.machinesid = share.machine_sid
					reply.netname = share.netname
					if len(sharebuffer.shares) >= 100:
						await self.websocket.send(sharebuffer.to_json())
						sharebuffer = NestOpSMBShareBuffRes()
						sharebuffer.token = cmd.token
				
				if len(sharebuffer.shares) > 0:
					await self.websocket.send(sharebuffer.to_json())
					sharebuffer = NestOpSMBShareBuffRes()
					sharebuffer.token = cmd.token
			
			for adid in res:
				#sending smb sessions
				logger.info('SESSIONS!')
				for session in self.db_session.query(NetSession).filter_by(ad_id = adid).all():
					await asyncio.sleep(0)
					reply = NestOpSMBSessionRes()
					reply.token = cmd.token
					reply.adid = session.ad_id
					reply.machinesid = session.machine_sid
					reply.username = session.username
					await self.websocket.send(reply.to_json())

			for adid in res:
				#sending groups
				logger.info('GROUPS!')
				groupbuffer = NestOpGroupBuffRes()
				groupbuffer.token = cmd.token
				qry = self.db_session.query(Group).filter_by(ad_id = adid)
				for group in windowed_query(qry, Group.id, 100):
					await asyncio.sleep(0)
					reply = NestOpGroupRes()
					reply.token = cmd.token
					reply.adid = group.ad_id
					reply.name = group.sAMAccountName
					reply.dn = group.dn
					reply.guid = group.objectGUID
					reply.sid = group.objectSid
					reply.description = group.description
					if group.adminCount is not None:
						reply.is_admin = int(group.adminCount)
					else:
						reply.is_admin = 0

					groupbuffer.groups.append(reply)

					if len(groupbuffer.groups) >= 100:
						await self.websocket.send(groupbuffer.to_json())
						groupbuffer = NestOpGroupBuffRes()
						groupbuffer.token = cmd.token
				
				if len(groupbuffer.groups) > 0:
					await self.websocket.send(groupbuffer.to_json())
					groupbuffer = NestOpGroupBuffRes()
					groupbuffer.token = cmd.token
			
			for adid in res:
				#sending edges
				logger.info('EDGES!')
				edgebuffer = NestOpEdgeBuffRes()
				edgebuffer.token = cmd.token

				qry = self.db_session.query(Edge).filter_by(ad_id = adid)
				for edge in windowed_query(qry, Edge.id, 100):
					await asyncio.sleep(0)
					reply = NestOpEdgeRes()
					reply.token = cmd.token
					reply.adid = edge.ad_id
					reply.graphid = edge.graph_id
					reply.src = self.lookup_oid(edge.src, edge.ad_id, cmd.token)
					reply.dst = self.lookup_oid(edge.dst, edge.ad_id, cmd.token)
					reply.label = edge.label
					if reply.src is None or reply.src == '':
						#print('ERROR!!! %s %s' % (edge.src, reply.src))
						continue

					edgebuffer.edges.append(reply)
					if len(edgebuffer.edges) >= 100:
						await self.websocket.send(edgebuffer.to_json())
						edgebuffer = NestOpEdgeBuffRes()
						edgebuffer.token = cmd.token
				
				if len(edgebuffer.edges) > 0:
					await self.websocket.send(edgebuffer.to_json())
					edgebuffer = NestOpEdgeBuffRes()
					edgebuffer.token = cmd.token


			await self.send_ok(cmd)
			logger.info('OK!')
		except Exception as e:
			await self.send_error(cmd, "Error! Reason: %s" % e)
			logger.exception('do_load_ad')

	
	async def do_kerberoast(self, cmd):
		pass

	async def do_smbsessions(self, cmd):
		pass

	async def do_pathshortest(self, cmd):
		pass

	async def do_pathda(self, cmd):
		if self.graph_id not in self.graphs:
			self.loadgraph(self.graph_id)
	
		da_sids = {}
		for res in self.db_session.query(Group).filter_by(ad_id = self.graphs[self.graph_id].domain_id).filter(Group.objectSid.like('%-512')).all():
			da_sids[res.objectSid] = 0
		
		if len(da_sids) == 0:
			return 'No domain administrator group found', 404
		
		res = GraphData()
		for sid in da_sids:
			res += self.graphs[self.graph_id].shortest_paths(None, sid)

		await self.send_result(cmd, res)

	async def do_add_cred(self, cmd):
		logger.info('do_add_cred')
		sc = StoredCred(cmd.username, cmd.password, cmd.description, cmd.domain, ownerid=None) #TODO: fill out owner id
		self.db_session.add(sc)
		self.db_session.commit()
		self.db_session.refresh(sc)
		cr = NestOpCredRes()
		cr.token = cmd.token
		cr.cid = sc.id
		cr.description = sc.description
		await self.websocket.send(cr.to_json())
		await self.send_ok(cmd)
		logger.info('OK!')


	async def do_get_cred(self, cmd):
		logger.info('do_get_cred')
		sc = self.db_session.query(StoredCred).get(cmd.cid)
		cr = NestOpCredRes()
		cr.token = cmd.token
		cr.cid = sc.id
		cr.description = sc.description
		await self.websocket.send(cr.to_json())
		await self.send_ok(cmd)
		logger.info('OK!')

	async def do_list_cred(self, cmd):
		logger.info('do_list_cred')
		ownerid = None
		for res in db.session.query(StoredCred.id, StoredCred.description).filter_by(ownerid = ownerid).all():
			await asyncio.sleep(0)
			cr = NestOpCredRes()
			cr.token = cmd.token
			cr.cid = res.id
			cr.description = res.description
			await self.websocket.send(cr.to_json())
		await self.send_ok(cmd)
		logger.info('OK!')

	async def do_add_target(self, cmd):
		logger.info('do_add_target')
		ownerid = None
		sc = CustomTarget(cmd.hostname, cmd.description, ownerid=ownerid) #TODO: fill out owner id
		self.db_session.add(sc)
		self.db_session.commit()
		self.db_session.refresh(sc)

		cr = NestOpTargetRes()
		cr.token = cmd.token
		cr.tid = sc.id
		cr.hostname = sc.hostname
		cr.description = sc.description
		await self.websocket.send(cr.to_json())
		await self.send_ok(cmd)
		logger.info('OK!')

	async def do_get_target(self, cmd):
		logger.info('do_get_target')
		sc = self.db_session.query(CustomTarget).get(cmd.tid)
		cr = NestOpTargetRes()
		cr.token = cmd.token
		cr.tid = sc.id
		cr.hostname = sc.hostname
		cr.description = sc.description
		await self.websocket.send(cr.to_json())
		await self.send_ok(cmd)
		logger.info('OK!')

	async def do_list_target(self, cmd):
		logger.info('do_list_target')
		ownerid = None
		for res in db.session.query(CustomTarget).filter_by(ownerid = ownerid).all():
			await asyncio.sleep(0)
			cr = NestOpTargetRes()
			cr.token = cmd.token
			cr.tid = res.id
			cr.hostname = res.hostname
			cr.description = res.description
			await self.websocket.send(cr.to_json())

		await self.send_ok(cmd)
		logger.info('OK!')

	async def __scanmonitor(self, cmd, results_queue):
		try:
			while True:
				try:
					data = await results_queue.get()
					if data is None:
						return
					
					tid, ip, port, status, err = data
					if status is True and err is None:
						reply = NestOpTCPScanRes()
						reply.token = cmd.token
						reply.host = str(ip)
						reply.port = int(port)
						reply.status = 'open'
						await self.websocket.send(reply.to_json())
				except asyncio.CancelledError:
					return
				except Exception as e:
					print('resmon died! %s' % e)

		except asyncio.CancelledError:
			return
		except Exception as e:
			print('resmon died! %s' % e)
			

	async def do_tcpscan(self, cmd):
		sm = None
		try:
			results_queue = asyncio.Queue()
			progress_queue = asyncio.Queue()
			sm = asyncio.create_task(self.__scanmonitor(cmd, results_queue))

			ps = JackdawPortScanner(results_queue=results_queue, progress_queue=progress_queue, backend='native')
			tg = ListTarget(cmd.targets)
			ps.add_portrange(cmd.ports)
			ps.add_target_gen(tg)
			_, err = await ps.run()
			if err is not None:
				await self.send_error(cmd, err)
				print(err)
			
			await self.send_ok(cmd)
		except Exception as e:
			await self.send_error(cmd, e)

		finally:
			if sm is not None:
				sm.cancel()


	async def run(self):
		try:
			self.msg_queue = asyncio.Queue()
			self.db_session = get_session(self.db_url)

			while True:
				try:
					cmd_raw = await self.websocket.recv()
					cmd = NestOpCmdDeserializer.from_json(cmd_raw)
					if cmd.cmd == NestOpCmd.GATHER:
						asyncio.create_task(self.do_gather(cmd))
					elif cmd.cmd == NestOpCmd.KERBEROAST:
						asyncio.create_task(self.do_kerberoast(cmd))
					elif cmd.cmd == NestOpCmd.SMBSESSIONS:
						asyncio.create_task(self.do_smbsessions(cmd))
					elif cmd.cmd == NestOpCmd.PATHSHORTEST:
						asyncio.create_task(self.do_pathshortest(cmd))
					elif cmd.cmd == NestOpCmd.PATHDA:
						asyncio.create_task(self.do_pathda(cmd))
					elif cmd.cmd == NestOpCmd.GETOBJINFO:
						asyncio.create_task(self.do_getobjinfo(cmd))
					elif cmd.cmd == NestOpCmd.LISTADS:
						asyncio.create_task(self.do_listads(cmd))
					elif cmd.cmd == NestOpCmd.CHANGEAD:
						asyncio.create_task(self.do_changead(cmd))
					elif cmd.cmd == NestOpCmd.LISTGRAPHS:
						asyncio.create_task(self.do_listgraphs(cmd))
					elif cmd.cmd == NestOpCmd.CHANGEGRAPH:
						asyncio.create_task(self.do_changegraph(cmd))
					elif cmd.cmd == NestOpCmd.TCPSCAN:
						asyncio.create_task(self.do_tcpscan(cmd))
					#elif cmd.cmd == NestOpCmd.LOADAD:
					#	asyncio.create_task(self.do_load_ad(cmd))
					elif cmd.cmd == NestOpCmd.LOADGRAPH:
						asyncio.create_task(self.do_load_graph(cmd))
					elif cmd.cmd == NestOpCmd.ADDCRED:
						asyncio.create_task(self.do_add_cred(cmd))
					elif cmd.cmd == NestOpCmd.GETCRED:
						asyncio.create_task(self.do_get_cred(cmd))
					elif cmd.cmd == NestOpCmd.LISTCRED:
						asyncio.create_task(self.do_list_cred(cmd))
					elif cmd.cmd == NestOpCmd.ADDTARGET:
						asyncio.create_task(self.do_add_target(cmd))
					elif cmd.cmd == NestOpCmd.GETTARGET:
						asyncio.create_task(self.do_get_target(cmd))
					elif cmd.cmd == NestOpCmd.LISTTARGET:
						asyncio.create_task(self.do_list_target(cmd))
					else:
						print('Unknown Command')

				except asyncio.CancelledError:
					return
				except Exception as e:
					traceback.print_exc()
					return

		except asyncio.CancelledError:
			return
		except Exception as e:
			print(e)