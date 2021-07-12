
import asyncio
import traceback
import websockets
import pathlib
import uuid
import os
import platform
from http import HTTPStatus
from urllib.parse import urlparse, parse_qs

from jackdaw.nest.ws.protocol.error import NestOpErr
from jackdaw.nest.ws.protocol.ok import NestOpOK
from jackdaw.nest.ws.protocol.cmdtypes import NestOpCmd
from jackdaw.nest.ws.protocol.wsnet.proxy import NestOpWSNETRouter


from jackdaw import logger
from jackdaw.nest.ws.operator.operator import NestOperator
from jackdaw.nest.ws.agent.agent import JackDawAgent
from jackdaw.nest.ws.guac.guacproxy import GuacProxy
from jackdaw.dbmodel import get_session
from jackdaw.dbmodel.adcomp import Machine
from jackdaw.dbmodel.dnslookup import DNSLookup
from jackdaw.dbmodel.credential import Credential
from jackdaw.dbmodel.storedcreds import StoredCred
from jackdaw.dbmodel.customtarget import CustomTarget
from jackdaw.nest.ws.remoteagent.wsnet.router import WSNETRouterHandler


# https://gist.github.com/artizirk/04eb23d957d7916c01ca632bb27d5436
# https://www.howtoforge.com/how-to-install-and-configure-guacamole-on-ubuntu-2004/

class NestWebSocketServer:
	def __init__(self, listen_ip, listen_port, db_url, work_dir, backend, ssl_ctx = None, enable_local_agent = True):
		self.listen_ip = listen_ip
		self.listen_port = listen_port
		self.ssl_ctx = ssl_ctx
		self.db_url = db_url
		self.db_session = None
		self.server = None
		self.server_in_q = None
		self.server_out_q = None
		self.operators = {}
		self.work_dir = pathlib.Path(work_dir)
		self.graph_backend = backend
		self.graph_type = None
		self.subprotocols = ['guacamole']

		self.guac_ip = '127.0.0.1'
		self.guac_port = 4822
		self.guac_html_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'guac', 'html')
		self.guac_html_rdp_path = os.path.join(self.guac_html_folder, 'rdp.html')
		self.guac_html_vnc_path = os.path.join(self.guac_html_folder, 'vnc.html')
		self.guac_html_ssh_path = os.path.join(self.guac_html_folder, 'ssh.html')
		self.guac_html_js_folder = os.path.join(self.guac_html_folder, 'js')

		#### AGENT related
		self.enable_local_agent = enable_local_agent
		self.agents = {}
		self.agent_in_q = None
		self.agent_out_q = None
		self.agent_cancellable_tasks = {} # agentid -> token -> task
		self.operator_cancellable_tasks = {} #operator_id -> token # this is used to cleanup running tasks when operator disconnects

		### sspiproxy related
		self.sspi_proxies = {}
		self.sspi_proxy_out_q = None

	async def __agent_task_terminate(self, cmd, cancel_token):
		await cancel_token.wait()
		del self.agent_cancellable_tasks[cmd.agent_id][cmd.token]
		print('DELETED TASK!')

	async def __add_agent_cancellable_task(self, cmd, task, cancel_token):
		if cmd.agent_id not in self.agent_cancellable_tasks:
			self.agent_cancellable_tasks[cmd.agent_id] = {}
		if cmd.token not in self.agent_cancellable_tasks[cmd.agent_id]:
			self.agent_cancellable_tasks[cmd.agent_id][cmd.token] = task
			asyncio.create_task(self.__agent_task_terminate(cmd, cancel_token))
		else:
			print('WAAAAAAAAAA! TOKEN RESUSE!!!!!! %s' % cmd.token)

	async def __handle_server_in(self):
		try:
			while True:
				operator_id, cmd = await self.server_out_q.get()
				if cmd.cmd == NestOpCmd.CANCEL:
					if cmd.agent_id not in self.agent_cancellable_tasks:
						await self.operators[operator_id].server_in_q.put(NestOpErr(cmd.token, 'Agent id not found!'))
						continue
					if cmd.token not in self.agent_cancellable_tasks[cmd.agent_id]:
						await self.operators[operator_id].server_in_q.put(NestOpErr(cmd.token, 'Token incorrect!'))
					self.agent_cancellable_tasks[cmd.agent_id][cmd.token].cancel()

				elif cmd.cmd == NestOpCmd.LISTAGENTS:
					# 
					for agentid in self.agents:
						agentreply = self.agents[agentid].get_list_reply(cmd)
						await self.operators[operator_id].server_in_q.put(agentreply)
					await self.operators[operator_id].server_in_q.put(NestOpOK(cmd.token))
				
				elif cmd.cmd == NestOpCmd.GATHER:
					# operator asks for a full gather to be executed on an agent
					if cmd.agent_id not in self.agents:
						await self.operators[operator_id].server_in_q.put(NestOpErr(cmd.token, 'Agent id not found!'))
						continue
					agent = self.agents[cmd.agent_id]
					await agent.do_gather(cmd, self.operators[operator_id].server_in_q, self.db_url, self.work_dir, True)
				
				elif cmd.cmd == NestOpCmd.WSNETLISTROUTERS:
					for router_id in self.sspi_proxies:
						notify = NestOpWSNETRouter()
						notify.token = cmd.token
						notify.url = self.sspi_proxies[router_id].url
						notify.router_id = router_id
						await self.operators[operator_id].server_in_q.put(notify)
					
					await self.operators[operator_id].server_in_q.put(NestOpOK(cmd.token))
				
				elif cmd.cmd == NestOpCmd.WSNETROUTERCONNECT:
					# operator is requesting the server to create a connection to a wsnet router
					proxy_id = str(uuid.uuid4())
					phandler = WSNETRouterHandler(cmd.url, proxy_id, self.sspi_proxy_out_q, self.db_session)
					asyncio.create_task(phandler.run())
					try:
						await asyncio.wait_for(phandler.connect_wait(), 5)
					except asyncio.exceptions.TimeoutError:
						await self.operators[operator_id].server_in_q.put(NestOpErr(cmd.token, 'Connection timed out!'))
						continue
					
					await self.operators[operator_id].server_in_q.put(NestOpOK(cmd.token))
					self.sspi_proxies[proxy_id] = phandler
					
					notify = NestOpWSNETRouter()
					notify.token = 0
					notify.url = cmd.url
					notify.router_id = proxy_id
					for operator_id in self.operators:
						await self.operators[operator_id].server_in_q.put(notify)

				elif cmd.cmd == NestOpCmd.SMBFILES:
					if cmd.agent_id not in self.agents:
						await self.operators[operator_id].server_in_q.put(NestOpErr(cmd.token, 'Agent id not found!'))
						continue
					agent = self.agents[cmd.agent_id]
					cancel_token = asyncio.Event()
					task = asyncio.create_task(agent.do_smbfiles(cmd, self.operators[operator_id].server_in_q, cancel_token))
					await self.__add_agent_cancellable_task(cmd, task, cancel_token)
					

		except Exception as e:
			traceback.print_exc()
	
	async def __handle_wsnet_router_in(self):
		try:
			while True:
				proxyid, datatype, data = await self.sspi_proxy_out_q.get()
				if datatype == 'AGENT_IN':
					#new agent connected via router
					self.agents[data.agent_id] = data
					asyncio.create_task(data.run())
					#notifying all operators
					for operator_id in self.operators:
						await self.operators[operator_id].server_in_q.put(data.get_list_reply(NestOpOK(0)))
					
		
		except Exception as e:
			traceback.print_exc()

	async def handle_wsnet_ext(self, ws, path):
		proxy_id = str(uuid.uuid4())
		phandler = WSNETRouterHandler(None, proxy_id, self.sspi_proxy_out_q, self.db_session, ext_ws = ws)
		asyncio.create_task(phandler.run())
					
		self.sspi_proxies[proxy_id] = phandler
					
		notify = NestOpWSNETRouter()
		notify.token = 0
		notify.url = 'EXT'
		notify.router_id = proxy_id
		for operator_id in self.operators:
			await self.operators[operator_id].server_in_q.put(notify)
		
		await phandler.disconnected_evt.wait() # this function needs to NOT return before the router disconnects otherwise the connection will be closed

	def get_target_address(self, ad_id, taget_sid):
		hostname = None
		if str(ad_id) == '0':
			res = self.db_session.query(CustomTarget).get(taget_sid)
			if res is not None:
				hostname = res.hostname
		else:
			res = self.db_session.query(Machine.dNSHostName).filter_by(objectSid = taget_sid).filter(Machine.ad_id == ad_id).first()
			if res is not None:
				hostname = res[0]
			else:
				res = self.db_session.query(DNSLookup.ip).filter_by(sid = taget_sid).filter(DNSLookup.ad_id == ad_id).first()
				if res is not None:
					hostname = res[0]

		print(hostname)
		return hostname

	def get_stored_cred(self, ad_id, user_sid):
		domain = None
		username = None
		password = None

		if str(ad_id) == '0':
			res = self.db_session.query(StoredCred).get(user_sid)
			
		else:
			res = self.db_session.query(Credential).filter_by(object_sid = user_sid).filter(Credential.ad_id == ad_id).first()
		
		if res is None:
			return False, None, None, None
		
		domain   = res.domain
		username = res.username
		password = res.password
		return True, domain, username, password

	async def handle_operator(self, websocket, path):
		remote_ip, remote_port = websocket.remote_address
		logger.info('Operator connected from %s:%s' % (remote_ip, remote_port))
		operator_id = str(uuid.uuid4())
		operator = NestOperator(operator_id, websocket, self.db_url, self.server_out_q, self.work_dir, self.graph_type)		
		self.operators[operator_id] = operator
		await operator.run()
		logger.info('Operator disconnected! %s:%s' % (remote_ip, remote_port))
	
	async def handle_guac(self, websocket, path, protocol):
		

		o = urlparse(path)
		q = parse_qs(o.query)
		print(q)
		
		#these parameters are mandatory!
		target_ad_id = q['tadid'][0]
		target_sid = q['target'][0]
		user_ad_id = q['uadid'][0]
		user_sid = q['user'][0]

		hostname = self.get_target_address(target_ad_id, target_sid)
		res, domain, username, password = self.get_stored_cred(user_ad_id, user_sid)
		#if res is False:
		#	print('Couldnt find credentials for user id %s' % user_sid)
		#	return

		gp = GuacProxy(self.guac_ip, self.guac_port, websocket)

		gp.video_width = q.get('width', ['1024'])[0]
		gp.video_height = q.get('height', ['768'])[0]
		gp.video_dpi = q.get('dpi', ['96'])[0]

		if protocol == 'rdp':
			port = q.get('port', ['3389'])[0]
			await gp.connect_rdp(
				hostname= hostname, 
				port = port,
				domain = domain,
				username= username,
				password= password
			)
		elif protocol == 'ssh':
			port = q.get('port', ['22'])[0]
			await gp.connect_ssh(
				hostname='10.10.10.101', 
				port = port,
				domain = None, 
				username= 'jackdaw', 
				password= 'jackdaw'
			)
		elif protocol == 'vnc':
			port = q.get('port', ['5900'])[0]
			await gp.connect_vnc(
				hostname='10.10.10.102', 
				port = port,
				domain = None, 
				username='test', 
				password= 'test'
			)
		
		return

	async def handle_incoming(self, websocket, path):
		print(path)
		if path == '/':
			await self.handle_operator(websocket, path)
		elif path.startswith('/guac/rdp'):
			await self.handle_guac(websocket, path, 'rdp')
		elif path.startswith('/guac/ssh'):
			await self.handle_guac(websocket, path, 'ssh')
		elif path.startswith('/guac/vnc'):
			await self.handle_guac(websocket, path, 'vnc')
		elif path.startswith('/wsnet/external'):
			await self.handle_wsnet_ext(websocket, path)
		else:
			logger.info('Cant handle path %s' % path)

	async def preprocess_request(self, path, request_headers):
		try:
			"""Serves a file when doing a GET request with a valid path."""

			if "Upgrade" in request_headers:
				return  # Probably a WebSocket connection
			
			print(path)
			#print(request_headers)
			response_headers = [
				('Server', 'JackDaw webserver'),
				('Connection', 'close'),
			]

			if path.startswith('/guac/js/guacamole-common-js/all.min.js'):
				with open(os.path.join(self.guac_html_js_folder, 'guacamole-common-js','all.min.js'), 'rb') as f:
					body = f.read()

				response_headers.append(('Content-Type', 'text/javascript'))
				return HTTPStatus.OK, response_headers, body


			elif path.startswith('/guac/rdp'):
				with open(self.guac_html_rdp_path, 'rb') as f:
					body = f.read()

				response_headers.append(('Content-Type', 'text/html'))
				return HTTPStatus.OK, response_headers, body
			
			elif path.startswith('/guac/vnc'):
				with open(self.guac_html_vnc_path, 'rb') as f:
					body = f.read()

				response_headers.append(('Content-Type', 'text/html'))
				return HTTPStatus.OK, response_headers, body

			elif path.startswith('/guac/ssh'):
				with open(self.guac_html_ssh_path, 'rb') as f:
					body = f.read()

				response_headers.append(('Content-Type', 'text/html'))
				return HTTPStatus.OK, response_headers, body

		except Exception as e:
			print(e)
			return HTTPStatus.INTERNAL_SERVER_ERROR, response_headers, b''

	async def run(self):
		if self.db_url is None:
			raise Exception('db_url must be either sqlalchemy url or an established db session')
		if isinstance(self.db_url, str):
			self.db_session = get_session(self.db_url)
		else:
			self.db_session = self.db_url

		if self.graph_backend.upper() == 'networkx'.upper():
			from jackdaw.nest.graph.backends.networkx.domaingraph import JackDawDomainGraphNetworkx
			self.graph_type = JackDawDomainGraphNetworkx
		elif self.graph_backend.upper() == 'igraph'.upper():
			from jackdaw.nest.graph.backends.igraph.domaingraph import JackDawDomainGraphIGraph
			self.graph_type = JackDawDomainGraphIGraph
		elif self.graph_backend.upper() == 'graphtools'.upper():
			from jackdaw.nest.graph.backends.graphtools.domaingraph import JackDawDomainGraphGrapthTools
			self.graph_type = JackDawDomainGraphGrapthTools

		pathlib.Path(self.work_dir).mkdir(parents=True, exist_ok=True)
		pathlib.Path(self.work_dir).joinpath('graphcache').mkdir(parents=True, exist_ok=True)

		self.server_in_q = asyncio.Queue()
		self.server_out_q = asyncio.Queue()
		self.sspi_proxy_out_q = asyncio.Queue()

		asyncio.create_task(self.__handle_server_in())
		asyncio.create_task(self.__handle_wsnet_router_in())

		if self.enable_local_agent is True:
			agentid = '0' #str(uuid.uuid4())
			internal_agent = JackDawAgent(agentid, 'internal', platform.system().upper(), self.db_session)
			self.agents[agentid] = internal_agent
			asyncio.create_task(internal_agent.run())


		#handler = functools.partial(process_request, os.getcwd())
		self.server = await websockets.serve(
			self.handle_incoming, 
			self.listen_ip, 
			self.listen_port, 
			ssl=self.ssl_ctx,
			process_request=self.preprocess_request,
			subprotocols=self.subprotocols
		)
		print('[+] Server is running!')
		await self.server.wait_closed()


async def amain(args):
	server = NestWebSocketServer(args.listen_ip, args.listen_port, args.sql, args.work_dir, args.backend, ssl_ctx = None)
	await server.run()

def main():
	import argparse
	parser = argparse.ArgumentParser(description='WS server')
	parser.add_argument('--sql', help='SQL connection string. When using SQLITE it works best with FULL FILE PATH!!!')
	parser.add_argument('--listen-ip',  default = '127.0.0.1', help='IP address to listen on')
	parser.add_argument('--listen-port',  type=int, default = 5001, help='IP address to listen on')
	parser.add_argument('--work-dir', default = './workdir', help='Working directory for caching and tempfiles')
	parser.add_argument('--backend', default = 'networkx', help='graph backend, pls dont change this')

	args = parser.parse_args()

	asyncio.run(amain(args))


if __name__ == '__main__':
	main()