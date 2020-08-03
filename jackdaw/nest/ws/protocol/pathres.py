import json

from jackdaw.utils.encoder import UniversalEncoder 
from jackdaw.nest.ws.protocol.cmdtypes import NestOpCmd

class Node:
	def __init__(self):
		self.domainid = None
		self.label = None
		self.type = None
		self.id = None
		self.md = None

class Edge:
	def __init__(self):
		self.src = None
		self.dst = None
		self.weight = None
		self.label = None

class NestOpPathRes:
	def __init__(self):
		self.cmd = NestOpCmd.PATHRES
		self.token = None
		self.nodes = []
		self.edges = []
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpPathRes()
		cmd.token = d['token']
		cmd.nodes = d['nodes']
		cmd.edges = d['edges']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpPathRes.from_dict(json.loads(jd))