
import json

from jackdaw.utils.encoder import UniversalEncoder 
from jackdaw.nest.ws.protocol.cmdtypes import NestOpCmd

class NestOpGetCred:
	def __init__(self):
		self.cmd = NestOpCmd.GETCRED
		self.cid = None
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpGetCred()
		cmd.token = d['token']
		cmd.cid = d['cid']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpGetCred.from_dict(json.loads(jd))

