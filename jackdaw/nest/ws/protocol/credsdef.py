import json

from jackdaw.utils.encoder import UniversalEncoder 
from jackdaw.nest.ws.protocol.cmdtypes import NestOpCmd

class NestOpCredsDef:
	def __init__(self):
		self.user_ad_id = None
		self.user_sid = None
		self.username = None
		self.domain = None
		self.password = None
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)

	@staticmethod
	def from_dict(d):
		cmd = NestOpCredsDef()
		cmd.username = d['username']
		cmd.domain = d['domain']
		cmd.password = d['password']
		cmd.user_ad_id = d['user_ad_id']
		cmd.user_sid = d['user_sid']
		return cmd
			
	@staticmethod
	def from_json(jd):
		return NestOpCredsDef.from_dict(json.loads(jd))