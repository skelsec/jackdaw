
import json

from jackdaw.utils.encoder import UniversalEncoder 
from jackdaw.nest.ws.protocol.cmdtypes import NestOpCmd

class NestOpTargetRes:
	def __init__(self):
		self.cmd = NestOpCmd.TARGETRES
		self.tid = None
		self.hostname = None
		self.description = None
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpTargetRes()
		cmd.token = d['token']
		cmd.tid = d['tid']
		cmd.hostname = d['hostname']
		cmd.description = d['description']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpTargetRes.from_dict(json.loads(jd))

