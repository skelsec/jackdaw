import json

from jackdaw.utils.encoder import UniversalEncoder 
from jackdaw.nest.ws.protocol.cmdtypes import NestOpCmd


class NestOpGroupRes:
	def __init__(self):
		self.cmd = NestOpCmd.GROUPRES
		self.token = None
		self.name = None
		self.adid = None
		self.dn = None
		self.guid = None
		self.sid = None
		self.description = None
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpGroupRes()
		cmd.token = d['token']
		if 'exclude' in d:
			cmd.exclude = d['exclude']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpGroupRes.from_dict(json.loads(jd))