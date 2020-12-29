
import json

from jackdaw.utils.encoder import UniversalEncoder 
from jackdaw.nest.ws.protocol.cmdtypes import NestOpCmd

class NestOpCredRes:
	def __init__(self):
		self.cmd = NestOpCmd.CREDRES
		self.cid = None
		self.description = None
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpCredRes()
		cmd.token = d['token']
		cmd.cid = d['tid']
		cmd.description = d['description']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpCredRes.from_dict(json.loads(jd))

