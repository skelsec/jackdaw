
import json

from jackdaw.utils.encoder import UniversalEncoder 
from jackdaw.nest.ws.protocol.cmdtypes import NestOpCmd

class NestOpListAD:
	def __init__(self):
		self.cmd = NestOpCmd.LISTADS
		self.token = None
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpListAD()
		cmd.token = d['token']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpListAD.from_dict(json.loads(jd))


class NestOpListADRes:
	def __init__(self):
		self.cmd = NestOpCmd.LISTADSRES
		self.token = None
		self.adids = []
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpListADRes()
		cmd.token = d['token']
		cmd.adids = d['adids']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpListADRes.from_dict(json.loads(jd))