
import json

from jackdaw.utils.encoder import UniversalEncoder 
from jackdaw.nest.ws.protocol.cmdtypes import NestOpCmd

class NestOpGetTarget:
	def __init__(self):
		self.cmd = NestOpCmd.GETTARGET
		self.tid = None
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpGetTarget()
		cmd.token = d['token']
		cmd.tid = d['tid']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpGetTarget.from_dict(json.loads(jd))

