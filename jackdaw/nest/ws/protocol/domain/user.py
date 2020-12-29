import json

from jackdaw.utils.encoder import UniversalEncoder 
from jackdaw.nest.ws.protocol.cmdtypes import NestOpCmd


class NestOpUserRes:
	def __init__(self):
		self.cmd = NestOpCmd.USERRES
		self.token = None
		self.name = None
		self.adid = None
		self.sid = None
		self.kerberoast = None
		self.asreproast = None
		self.nopassw = None
		self.cleartext = None
		self.smartcard = None
		self.active = None
		self.description = None
		self.is_admin = False
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpUserRes()
		cmd.token = d['token']
		if 'exclude' in d:
			cmd.exclude = d['exclude']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpUserRes.from_dict(json.loads(jd))


class NestOpUserBuffRes:
	def __init__(self):
		self.cmd = NestOpCmd.USERBUFFRES
		self.token = None
		self.users = [] #NestOpEdgeRes
	
	def to_dict(self):
		return {
			'cmd' : self.cmd.value,
			'token' : self.token,
			'users' : [users.to_dict() for users in self.users],
		}
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpUserBuffRes()
		cmd.token = d['token']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpUserBuffRes.from_dict(json.loads(jd))