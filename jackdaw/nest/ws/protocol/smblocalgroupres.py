import json

from jackdaw.utils.encoder import UniversalEncoder 
from jackdaw.nest.ws.protocol.cmdtypes import NestOpCmd


class NestOpSMBLocalGroupRes:
	def __init__(self):
		self.cmd = NestOpCmd.SMBLOCALGROUPRES
		self.token = None
		self.adid = None
		self.machinesid = None
		self.usersid = None
		self.groupname = None
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpSMBLocalGroupRes()
		cmd.token = d['token']
		cmd.adid = d['adid']
		cmd.machinesid = d['machinesid']
		cmd.usersid = d['usersid']
		cmd.groupname = d['groupname']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpSMBLocalGroupRes.from_dict(json.loads(jd))