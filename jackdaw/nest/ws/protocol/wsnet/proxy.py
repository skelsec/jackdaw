
import json

from jackdaw.utils.encoder import UniversalEncoder 
from jackdaw.nest.ws.protocol.cmdtypes import NestOpCmd

class NestOpWSNETRouter:
	def __init__(self):
		self.cmd = NestOpCmd.WSNETROUTER
		self.url = None
		self.router_id = None
		self.token = None
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpWSNETRouter()
		cmd.token = d['token']
		cmd.router_id = d['router_id']
		cmd.url = d['url']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpWSNETRouter.from_dict(json.loads(jd))