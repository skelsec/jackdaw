import json

from jackdaw.utils.encoder import UniversalEncoder 
from jackdaw.nest.ws.protocol.cmdtypes import NestOpCmd


class NestOpSMBShareRes:
	def __init__(self):
		self.cmd = NestOpCmd.SMBSHARERES
		self.token = None
		self.adid = None
		self.machinesid = None
		self.netname = None
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpSMBShareRes()
		cmd.token = d['token']
		cmd.adid = d['adid']
		cmd.machinesid = d['machinesid']
		cmd.netname = d['netname']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpSMBShareRes.from_dict(json.loads(jd))



class NestOpSMBShareBuffRes:
	def __init__(self):
		self.cmd = NestOpCmd.SMBSHAREBUFFRES
		self.token = None
		self.shares = [] #NestOpEdgeRes
	
	def to_dict(self):
		return {
			'cmd' : self.cmd.value,
			'token' : self.token,
			'shares' : [shares.to_dict() for shares in self.shares],
		}
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpSMBShareBuffRes()
		cmd.token = d['token']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpSMBShareBuffRes.from_dict(json.loads(jd))