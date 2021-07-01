import json

from jackdaw.utils.encoder import UniversalEncoder 
from jackdaw.nest.ws.protocol.cmdtypes import NestOpCmd


class NestOpNotify:
	def __init__(self):
		self.cmd = NestOpCmd.NOTIFY
		self.token = 0 #token 0 is notify
		self.level = None
		self.msg = None
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpNotify()
		cmd.level = d['level']
		cmd.msg = d['msg']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpNotify.from_dict(json.loads(jd))