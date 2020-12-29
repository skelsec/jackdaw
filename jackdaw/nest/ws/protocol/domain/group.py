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
		self.is_admin = None
	
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

class NestOpGroupBuffRes:
	def __init__(self):
		self.cmd = NestOpCmd.GROUPBUFFRES
		self.token = None
		self.groups = [] #NestOpEdgeRes
	
	def to_dict(self):
		return {
			'cmd' : self.cmd.value,
			'token' : self.token,
			'groups' : [groups.to_dict() for groups in self.groups],
		}
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpGroupBuffRes()
		cmd.token = d['token']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpGroupBuffRes.from_dict(json.loads(jd))