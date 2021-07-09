import json

from jackdaw.utils.encoder import UniversalEncoder 
from jackdaw.nest.ws.protocol.cmdtypes import NestOpCmd


class NestOpTargetDef:
	def __init__(self):
		self.hostname = None
		self.ip = None
		self.machine_ad_id = None
		self.machine_sid = None

	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpTargetDef()
		cmd.hostname = d['hostname']
		cmd.ip = d['ip']
		cmd.machine_ad_id = d['machine_ad_id']
		cmd.machine_sid = d['machine_sid']
		return cmd

	
	@staticmethod
	def from_json(jd):
		return NestOpTargetDef.from_dict(json.loads(jd))