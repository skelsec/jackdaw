import json

from jackdaw.utils.encoder import UniversalEncoder 
from jackdaw.nest.ws.protocol.cmdtypes import NestOpCmd
from jackdaw.nest.ws.protocol.credsdef import NestOpCredsDef
from jackdaw.nest.ws.protocol.targetdef import NestOpTargetDef


class NestOpKerberosTGS:
	def __init__(self):
		self.cmd = NestOpCmd.KERBEROSTGS
		self.token = None
		self.agent_id = None
		self.target:NestOpTargetDef = None
		self.creds:NestOpCredsDef = None
		self.spn:str = None
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpKerberosTGS()
		cmd.token = d['token']
		cmd.agent_id = d['agent_id']
		cmd.target = NestOpTargetDef.from_dict(d['target'])
		cmd.creds = NestOpCredsDef.from_dict(d['creds'])
		cmd.spn = d['spn']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpKerberosTGS.from_dict(json.loads(jd))


class NestOpKerberosTGSRes:
	def __init__(self):
		self.cmd = NestOpCmd.KERBEROSTGSRES
		self.token = None
		self.ticket = None
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpKerberosTGSRes()
		cmd.token = d['token']
		cmd.ticket = d['ticket']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpKerberosTGSRes.from_dict(json.loads(jd))