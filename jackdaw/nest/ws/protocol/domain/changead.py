

import json

from jackdaw.utils.encoder import UniversalEncoder 
from jackdaw.nest.ws.protocol.cmdtypes import NestOpCmd

class NestOpChangeAD:
	def __init__(self):
		self.cmd = NestOpCmd.CHANGEAD
		self.token = None
		self.adid = None
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpChangeAD()
		cmd.adid = d['adid']
		cmd.token = d['token']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpChangeAD.from_dict(json.loads(jd))