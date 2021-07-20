import json

from jackdaw.utils.encoder import UniversalEncoder 
from jackdaw.nest.ws.protocol.cmdtypes import NestOpCmd


class NestOpPathOwned:
	def __init__(self):
		self.cmd = NestOpCmd.PATHOWNED
		self.token = None
		self.graphid = None
		self.dst = None #dst can be 'ANY' or 'DA' or 'HVT'
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpPathOwned()
		cmd.token = d['token']
		cmd.graphid = int(d['graphid'])
		cmd.dst = d['dst']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpPathOwned.from_dict(json.loads(jd))