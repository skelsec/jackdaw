
import asyncio
import websockets

from jackdaw.nest.ws.protocol.ok import NestOpOK
from jackdaw.nest.ws.protocol.intercom.intercom import IntercomAgent, IntercomListAgents
from jackdaw.nest.ws.protocol.cmdtypes import NestOpCmd


class InterComPacket:
	def __init__(self):
		self.operatorid = None
		self.agentid = None
		self.data = None

class InterComManager:
	def __init__(self):
		self.agents = {}
		self.operators = {}
		self.agent_in_q = None
		self.operator_in_q = None

		self.__agentid_ctr = 100
		self.__operator_ctr = 100
		self.__opmsgtable = {}
		self.__agentmsgtable = {}
		self.__agent_in_handle_task = None
		self.__operator_in_handle_task = None

	def get_agentid(self):
		t = self.__agentid_ctr
		self.__agentid_ctr += 1
		return t
	
	def get_operatorid(self):
		t = self.__operator_ctr
		self.__operator_ctr += 1
		return t

	async def __handle_agent_in(self):
		while True:
			packet = self.agent_in_q.get()
			if packet.operatorid is None: #broadcast from agent
				for operatorid in self.operators:
					await self.operators[operatorid].intercom_q_in.put(packet)
				continue
			
			if packet.operatorid not in self.operators:
				print('Unknown target operator!')
				# todo: signal to agent
				continue
			
			await self.operators[packet.operatorid].intercom_q_in.put(packet)
			
	async def __handle_operator_in(self):
		while True:
			packet = self.operator_in_q.get()
			if packet.agentid is None: #broadcast message
				for agentid in self.agents:
					await self.agents[agentid].put(packet)
				continue
			
			if packet.agent == 0:
				# message to the intercom
				if packet.data.cmd == NestOpCmd.INTERCOMAGENTLIST:
					for agentid in self.agents:
						reply = IntercomAgent()
						reply.token = packet.data.token
						reply.agentid = agentid
						reply.agenttype = self.agents[agentid].agenttype
						self.operators[packet.operatorid].intercom_q_in.put(reply)
					
					reply = NestOpOK()
					reply.token = packet.data.token
					self.operators[packet.operatorid].intercom_q_in.put(reply)
				
				continue


			if packet.agentid not in self.agents:
				print('Unknown target agent!')
				# todo: signal to operator
				continue
			
			await self.agents[packet.agentid].intercom_q_in.put(packet)

	async def add_agent(self, agent):
		agent.agentid = self.get_agentid()
		agent.intercom_q_in = self.agent_in_q
		self.agents[agent.agentid] = agent


	async def add_operator(self, operator):
		pass

	async def run(self):
		self.agent_in_q = asyncio.Queue()
		self.operator_in_q = asyncio.Queue()
		self.__agent_in_handle_task = asyncio.create_task(self.__handle_agent_in())
		self.__operator_in_handle_task = asyncio.create_task(self.__handle_operator_in())


class SSPIProxyAgent:
	def __init__(self):
		

class SSPIProxyOperator:
	def __init__(self, server_url, agentid, intercom_q_in, intercom_q_out):
		self.agenttype = 'sspiproxyoperator'
		self.agentid = agentid
		self.server_url = server_url
		self.intercom_q_in = intercom_q_in
		self.intercom_q_out = intercom_q_out
		self.agents = {}

	async def __handle_intercom_in(self):
		while True:
			packet = await self.intercom_q_in.get()
			if packet.agentid is None:
				#dunno what to do with broadcast data here...
				continue


	async def run(self):
		try:
			while True:
				try:
					self.ws = await websockets.connect(self.server_url)
				except Exception as e:
					print('Failed to connect to server!')
					continue

				try:
					data = await self.ws.recv()
					cmd = CMD.from_bytes(data)
					if cmd.type == CMDType.AGENTINFO:
						await self.intercom_q_out.put('new agent in!')
						
				except Exception as e:
					print('run exception!')
					print(e)
					break

		except Exception as e:
			print(e)
			return