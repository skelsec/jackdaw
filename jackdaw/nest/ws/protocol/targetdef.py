import json

from jackdaw.utils.encoder import UniversalEncoder 
from jackdaw.nest.ws.protocol.cmdtypes import NestOpCmd


class NestOpTargetDef:
	def __init__(self):
		self.adid = None
		self.sid = None
		self.timeout = 5

	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpTargetDef()
		cmd.adid = d['adid']
		cmd.sid = d['sid']
		cmd.timeout = int(d['timeout'])
		return cmd

	
	@staticmethod
	def from_json(jd):
		return NestOpTargetDef.from_dict(json.loads(jd))
	
	def __repr__(self):
		return 'NestOpTargetDef: adid: %s sid: %s timeout: %s' % (self.adid, self.sid, self.timeout)