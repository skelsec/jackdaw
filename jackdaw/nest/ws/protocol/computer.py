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