import json

from jackdaw.utils.encoder import UniversalEncoder 
from jackdaw.nest.ws.protocol.cmdtypes import NestOpCmd


class NestOpSMBFileRes:
	def __init__(self):
		self.cmd = NestOpCmd.SMBFILERES
		self.token = None
		self.machine_ad_id = None
		self.machine_sid = None
		self.otype = None
		self.unc_path = None

	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpSMBFileRes()
		cmd.token = d['token']
		cmd.machine_ad_id = d['machine_ad_id']
		cmd.machine_sid = d['machine_sid']
		cmd.otype = d['otype']
		cmd.unc_path = d['unc_path']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpSMBFileRes.from_dict(json.loads(jd))
