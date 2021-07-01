import json

from jackdaw.utils.encoder import UniversalEncoder 
from jackdaw.nest.ws.protocol.cmdtypes import NestOpCmd
class NestOpErr:
	def __init__(self, token = None, resaon = None):
		self.cmd = NestOpCmd.ERR
		self.token = token
		self.reason = resaon
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpErr()
		cmd.token = d['token']
		if 'reason' in d:
			cmd.reason = d['reason']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpErr.from_dict(json.loads(jd))

