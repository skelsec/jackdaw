import json

from jackdaw.utils.encoder import UniversalEncoder 
from jackdaw.nest.ws.protocol.cmdtypes import NestOpCmd


class NestOpOK:
	def __init__(self):
		self.cmd = NestOpCmd.OK
		self.token = None
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpOK()
		cmd.token = d['token']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpOK.from_dict(json.loads(jd))

