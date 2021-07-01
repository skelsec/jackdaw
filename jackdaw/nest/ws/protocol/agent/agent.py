import json

from jackdaw.utils.encoder import UniversalEncoder 
from jackdaw.nest.ws.protocol.cmdtypes import NestOpCmd

class NestOpListAgents:
	def __init__(self):
		self.cmd = NestOpCmd.LISTAGENTS
		self.token = None
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpListAgents()
		cmd.token = d['token']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpListAgents.from_dict(json.loads(jd))

class NestOpAgent:
	def __init__(self):
		self.cmd = NestOpCmd.AGENT
		self.token = None
		self.agentid = None
		self.agenttype = None
		self.platform = None
		self.pid = None
		self.username = None
		self.domain = None
		self.logonserver = None
		self.cpuarch = None
		self.hostname = None
		self.usersid = None
		self.internal_id = None
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpAgent()
		cmd.token = d['token']
		cmd.agentid = d['agentid']
		cmd.agenttype = d['agenttype']
		cmd.platform = d['platform']
		cmd.pid = d['pid']
		cmd.username = d['username']
		cmd.domain = d['domain']
		cmd.logonserver = d['logonserver']
		cmd.cpuarch = d['cpuarch']
		cmd.hostname = d['hostname']
		cmd.usersid = d['usersid']
		cmd.internal_id = d['internal_id']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpAgent.from_dict(json.loads(jd))
