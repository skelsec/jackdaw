import uuid
import asyncio
import websockets
import traceback

from wsnet.protocol import *
from jackdaw.nest.ws.agent.agent import JackDawAgent

class WSNETRouterHandler:
	def __init__(self, server_url, proxy_id, server_out_q, db_session, ext_ws = None):
		self.connected_evt = asyncio.Event()
		self.disconnected_evt = asyncio.Event()
		self.proxyid = proxy_id
		self.server_url = server_url
		self.server_in_q = None
		self.server_out_q = server_out_q
		self.db_session = db_session
		self.agents = {}
		self.__token = 1
		self.reply_dispatch_table = {}
		self.ws = ext_ws
	
	def __get_token(self):
		t = self.__token
		self.__token += 1
		return str(t)

	async def __handle_server_in(self):
		while True:
			packet = await self.server_in_q.get()
			print(packet)

	async def __handle_router_in(self):
		while True:
			try:
				print(1)
				data = await self.ws.recv()
				print('DATA IN -> %s' % data)
				cmd = CMD.from_bytes(data)
				
				if cmd.type == CMDType.AGENTINFO:
					agent_id = str(uuid.uuid4())
					agent_type = 'wsnet'

					agent = JackDawAgent(
						agent_id, 
						agent_type, 
						'windows',#agent_platform, 
						self.db_session,
						pid = 0, 
						username = cmd.username, 
						domain = cmd.domain, 
						logonserver = cmd.logonserver, 
						cpuarch = cmd.cpuarch, 
						hostname = cmd.hostname, 
						usersid = cmd.usersid,
						internal_id = cmd.agentid.hex(),
					)
					agent.connection_via.append(self.proxyid)
		
					await self.server_out_q.put((self.proxyid, 'AGENT_IN', agent))

				else:
					print('WSNET router got unknown message! %s' % cmd.type)

			except Exception as e:
				traceback.print_exc()
				#print('Reciever error %s' % e)
				return

	async def connect_wait(self):
		await self.connected_evt.wait()

	async def list_agents(self):
		try:
			agentid = b'\x00'*16 #router's info channel
			cmd = WSNListAgents(b'\x00'*16)
			await self.ws.send(OPCMD(agentid, cmd).to_bytes())
		
		except Exception as e:
			traceback.print_exc()
			return

	async def run(self):
		try:
			self.server_in_q = asyncio.Queue()
			asyncio.create_task(self.__handle_server_in())

			if self.ws is None:
				try:
					self.ws = await websockets.connect(self.server_url)
				except Exception as e:
					print('Failed to connect to server!')
					return

			self.connected_evt.set()
			asyncio.create_task(self.list_agents())
			await self.__handle_router_in()

		except Exception as e:
			print(e)
			return
		finally:
			self.disconnected_evt.set()