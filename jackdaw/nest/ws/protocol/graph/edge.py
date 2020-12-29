import json

from jackdaw.utils.encoder import UniversalEncoder 
from jackdaw.nest.ws.protocol.cmdtypes import NestOpCmd


class NestOpEdgeRes:
	def __init__(self):
		self.cmd = NestOpCmd.EDGERES
		self.token = None
		self.adid = None
		self.graphid = None
		self.src = None #oid!
		self.dst = None #oid!
		self.weight = 1
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpEdgeRes()
		cmd.token = d['token']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpEdgeRes.from_dict(json.loads(jd))

class NestOpEdgeBuffRes:
	def __init__(self):
		self.cmd = NestOpCmd.EDGEBUFFRES
		self.token = None
		self.edges = [] #NestOpEdgeRes
	
	def to_dict(self):
		return {
			'cmd' : self.cmd.value,
			'token' : self.token,
			'edges' : [edge.to_dict() for edge in self.edges],
		}
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpEdgeBuffRes()
		cmd.token = d['token']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpEdgeBuffRes.from_dict(json.loads(jd))

