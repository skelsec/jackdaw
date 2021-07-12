
import json

from jackdaw.utils.encoder import UniversalEncoder 
from jackdaw.nest.ws.protocol.cmdtypes import NestOpCmd


class NestOpWSNETListRouters:
	def __init__(self):
		self.cmd = NestOpCmd.WSNETLISTROUTERS
		self.token = None
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpWSNETListRouters()
		cmd.token = d['token']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpWSNETListRouters.from_dict(json.loads(jd))