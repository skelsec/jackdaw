import json

from jackdaw.utils.encoder import UniversalEncoder 
from jackdaw.nest.ws.protocol.cmdtypes import NestOpCmd

class IntercomListAgents:
	def __init__(self):
		self.cmd = NestOpCmd.INTERCOMLISTAGENTS
		self.token = None
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = IntercomListAgents()
		cmd.token = d['token']
		return cmd

	@staticmethod
	def from_json(jd):
		return IntercomListAgents.from_dict(json.loads(jd))



class IntercomAgent:
	def __init__(self):
		self.cmd = NestOpCmd.INTERCOMAGENT
		self.token = None
		self.agentid = None
		self.agenttype = None
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = IntercomAgent()
		cmd.token = d['token']
		cmd.agentid = d['agentid']
		cmd.agenttype = d['agenttype']
		return cmd

	@staticmethod
	def from_json(jd):
		return IntercomAgent.from_dict(json.loads(jd))
