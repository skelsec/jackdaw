import json

from jackdaw.utils.encoder import UniversalEncoder 
from jackdaw.nest.ws.protocol.cmdtypes import NestOpCmd


class NestOpSMBSessionRes:
	def __init__(self):
		self.cmd = NestOpCmd.SMBSESSIONRES
		self.token = None
		self.adid = None
		self.machinesid = None
		self.username = None
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpSMBSessionRes()
		cmd.token = d['token']
		cmd.adid = d['ad_id']
		cmd.machinesid = d['machine_sid']
		cmd.username = d['username']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpSMBSessionRes.from_dict(json.loads(jd))