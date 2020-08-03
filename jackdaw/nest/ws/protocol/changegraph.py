import json

from jackdaw.utils.encoder import UniversalEncoder 
from jackdaw.nest.ws.protocol.cmdtypes import NestOpCmd

class NestOpChangeGraph:
	def __init__(self):
		self.cmd = NestOpCmd.CHANGEGRAPH
		self.token = None
		self.graphid = None
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpChangeGraph()
		cmd.token = d['token']
		cmd.graphid = d['graphid']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpChangeGraph.from_dict(json.loads(jd))