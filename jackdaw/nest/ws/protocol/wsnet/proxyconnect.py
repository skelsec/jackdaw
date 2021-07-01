
import json

from jackdaw.utils.encoder import UniversalEncoder 
from jackdaw.nest.ws.protocol.cmdtypes import NestOpCmd


class NestOpWSNETRouterconnect:
	def __init__(self):
		self.cmd = NestOpCmd.WSNETROUTERCONNECT
		self.url = None
		self.token = None
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpWSNETRouterconnect()
		cmd.token = d['token']
		cmd.url = d['url']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpWSNETRouterconnect.from_dict(json.loads(jd))