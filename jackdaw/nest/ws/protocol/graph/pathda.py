import json

from jackdaw.utils.encoder import UniversalEncoder 
from jackdaw.nest.ws.protocol.cmdtypes import NestOpCmd


class NestOpPathDA:
	def __init__(self):
		self.cmd = NestOpCmd.PATHDA
		self.token = None
		self.graphid = None
		self.exclude = []
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpPathDA()
		cmd.token = d['token']
		cmd.graphid = int(d['graphid'])
		if 'exclude' in d:
			cmd.exclude = d['exclude']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpPathDA.from_dict(json.loads(jd))