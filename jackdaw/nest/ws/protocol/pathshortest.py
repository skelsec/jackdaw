import json

from jackdaw.utils.encoder import UniversalEncoder 
from jackdaw.nest.ws.protocol.cmdtypes import NestOpCmd


class NestOpPathShortest:
	def __init__(self):
		self.cmd = NestOpCmd.PATHSHORTEST
		self.token = None
		self.to_sid = None
		self.from_sid = False
		self.exclude = []
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpPathShortest()
		cmd.token = d['token']
		if 'to_sid' in d:
			cmd.to_sid = d['to_sid']
		if 'from_sid' in d:
			cmd.from_sid = d['from_sid']
		if 'exclude' in d:
			cmd.exclude = d['exclude']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpPathShortest.from_dict(json.loads(jd))

