import json

from jackdaw.utils.encoder import UniversalEncoder 
from jackdaw.nest.ws.protocol.cmdtypes import NestOpCmd

class NestOpObjHVT:
	def __init__(self):
		self.cmd = NestOpCmd.OBJHVT
		self.token = None
		self.graphid = None
		self.adid = None
		self.otype = None
		self.oid = None
		self.set = None # True = mark user/machine/group etc as high-value-target, False = clear high-value-target status
		
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpObjHVT()
		cmd.token = d['token']
		cmd.graphid = d['graphid']
		cmd.adid = d['adid']
		cmd.otype = d['otype']
		cmd.oid = d['oid']
		cmd.set = d['set']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpObjHVT.from_dict(json.loads(jd))
