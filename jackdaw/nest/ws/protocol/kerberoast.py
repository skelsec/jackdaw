import json

from jackdaw.utils.encoder import UniversalEncoder 
from jackdaw.nest.ws.protocol.cmdtypes import NestOpCmd

class NestOpKerberoast:
	def __init__(self):
		self.cmd = NestOpCmd.KERBEROAST
		self.token = None
		self.kerberos_url = None
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpKerberoast()
		cmd.token = d['token']
		cmd.kerberos_url = d['kerberos_url']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpKerberoast.from_dict(json.loads(jd))
