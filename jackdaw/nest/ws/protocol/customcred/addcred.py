
import json

from jackdaw.utils.encoder import UniversalEncoder 
from jackdaw.nest.ws.protocol.cmdtypes import NestOpCmd

class NestOpAddCred:
	def __init__(self):
		self.cmd = NestOpCmd.ADDCRED
		self.token = None
		self.username = None
		self.domain = None
		self.password = None
		self.description = None
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpAddCred()
		cmd.token = d['token']
		cmd.username = d['username']
		cmd.domain = d['domain']
		cmd.password = d['password']
		cmd.description = d['description']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpAddCred.from_dict(json.loads(jd))

