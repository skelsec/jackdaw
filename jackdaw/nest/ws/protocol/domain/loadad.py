import json

from jackdaw.utils.encoder import UniversalEncoder 
from jackdaw.nest.ws.protocol.cmdtypes import NestOpCmd


class NestOpLoadAD:
	def __init__(self):
		self.cmd = NestOpCmd.LOADAD
		self.token = None
		self.adid = None
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpLoadAD()
		cmd.token = d['token']
		cmd.adid = d['adid']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpLoadAD.from_dict(json.loads(jd))