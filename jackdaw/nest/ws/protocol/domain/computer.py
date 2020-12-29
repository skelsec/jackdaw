import json

from jackdaw.utils.encoder import UniversalEncoder 
from jackdaw.nest.ws.protocol.cmdtypes import NestOpCmd


class NestOpComputerRes:
	def __init__(self):
		self.cmd = NestOpCmd.COMPUTERRES
		self.token = None
		self.name = None
		self.adid = None
		self.sid = None
		self.domainname = None
		self.ostype = None
		self.osver = None
		self.active = None
		self.description = None
		self.computertype = None
		self.isoutdated = 0
		self.is_admin = None
		self.isinactive = None

	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpComputerRes()
		cmd.token = d['token']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpComputerRes.from_dict(json.loads(jd))


class NestOpComputerBuffRes:
	def __init__(self):
		self.cmd = NestOpCmd.COMPUTERBUFFRES
		self.token = None
		self.computers = [] #NestOpEdgeRes
	
	def to_dict(self):
		return {
			'cmd' : self.cmd.value,
			'token' : self.token,
			'computers' : [computers.to_dict() for computers in self.computers],
		}
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpComputerBuffRes()
		cmd.token = d['token']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpComputerBuffRes.from_dict(json.loads(jd))