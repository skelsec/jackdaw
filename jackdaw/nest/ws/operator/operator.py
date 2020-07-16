import asyncio
import multiprocessing

from jackdaw.dbmodel.adinfo import ADInfo
from jackdaw.dbmodel.edgelookup import EdgeLookup
from jackdaw.dbmodel.aduser import ADUser
from jackdaw.dbmodel.adgroup import Group
from jackdaw.dbmodel import create_db, get_session

from jackdaw.gatherer.gatherer import Gatherer
from jackdaw.gatherer.scanner.scanner import *
from jackdaw.nest.ws.operator.protocol import *

from jackdaw.nest.graph.graphdata import GraphData

class NestOperator:
	def __init__(self, websocket, db_url, global_msg_queue, work_dir, graph_type):
		self.websocket = websocket
		self.db_url = db_url
		self.db_session = None
		self.global_msg_queue = global_msg_queue
		self.work_dir = work_dir
		self.msg_queue = None
		self.ad_id = None
		self.show_progress = True #prints progress to console?
		self.graphs = {}
		self.graph_type = graph_type
		self.graph_id = None

	def loadgraph(self, graphid):
		graphid = int(graphid)
		graph_cache_dir = self.work_dir.joinpath('graphcache')
		graph_dir = graph_cache_dir.joinpath(str(graphid))
		if graph_dir.exists() is False:
			raise Exception('Graph cache dir doesnt exists!')
		else:
			self.graphs[graphid] = self.graph_type.load(self.db_session, graphid, graph_dir)
		
		return True

	def listgraphs(self):
		t = []
		graph_cache_dir = self.work_dir.joinpath('graphcache')
		x = [f for f in graph_cache_dir.iterdir() if f.is_dir()]
		for d in x:
			t.append(int(str(d.name)))
		return t

	async def do_listgraphs(self, cmd):
		res = self.listgraphs()
		await self.send_result(cmd, res)

	async def do_changegraph(self, cmd):
		if cmd.graphid not in self.listgraphs():
			await self.send_error(cmd, 'Graph id not found')

		self.graph_id = int(cmd.graphid)
		await self.send_ok(cmd)

	async def progess_outgoing(self):
		try:
			while True:
				try:
					msg = await self.msg_queue.get()
					print('progress %s' % msg)
					
					await self.websocket.send(msg.to_dict())

				except asyncio.CancelledError:
					return
				except Exception as e:
					print(e)
					return

		except asyncio.CancelledError:
			return
		except Exception as e:
			print(e)

	async def send_error(self, ocmd, reason = None):
		reply = NestOpErr()
		reply.token = ocmd.token
		reply.reason = reason
		await self.websocket.send(reply.to_json())
	
	async def send_ok(self, ocmd):
		reply = NestOpOK()
		reply.token = ocmd.token
		await self.websocket.send(reply.to_json())

	async def send_result(self, ocmd, data):
		try:
			print('here')
			reply = NestOpResult()
			reply.restype = ocmd.cmd
			reply.token = ocmd.token
			reply.data = data
			print(reply.to_json())
			await self.websocket.send(reply.to_json())
		except Exception as e:
			print(e)
	

	async def do_gather(self, cmd):
		with multiprocessing.Pool() as mp_pool:
			gatherer = Gatherer(
				self.db,
				self.work_dir,
				cmd.ldap_url, 
				cmd.smb_url,
				kerb_url=cmd.kerberos_url,
				ldap_worker_cnt=cmd.ldap_workers, 
				smb_worker_cnt=cmd.smb_workers, 
				mp_pool=mp_pool, 
				smb_gather_types=['all'], 
				progress_queue=self.msg_queue, 
				show_progress=self.show_progress,
				calc_edges=True,
				ad_id=None,
				dns=cmd.dns
			)
			res, err = await gatherer.run()
			if err is not None:
				print('gatherer returned error')
				await self.send_error()
	
	async def do_listads(self, cmd):
		res = []
		for i in self.db_session.query(ADInfo.id).all():
			print(i)
			res.append(i[0])
		
		await self.send_result(cmd, res)
		#NestOpCmd.LISTADS : NestOpListAD,
	
	async def do_changead(self, cmd):
		res = self.db_session.query(ADInfo).get(cmd.adid)
		print(res)
		if res is None:
			await self.send_error(cmd, 'No such AD in database')
			return
		
		self.ad_id = res.id
		await self.send_ok(cmd)

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
	
	async def __scanmonitor(self, cmd, results_queue):
		while True:
			data = await results_queue.get()
			if data is None:
				return
			
			tid, ip, port, status, err = data
			if status is True and err is None:
				await self.send_result(cmd, [str(ip), int(port)])
			

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
					print(cmd_raw)
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
					else:
						print('Unknown Command')

				except asyncio.CancelledError:
					return
				except Exception as e:
					print(e)
					return

		except asyncio.CancelledError:
			return
		except Exception as e:
			print(e)