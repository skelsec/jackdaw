
import json

from jackdaw.utils.encoder import UniversalEncoder 
from jackdaw.nest.ws.protocol.cmdtypes import NestOpCmd


class NestOpListGraphRes:
	def __init__(self):
		self.cmd = NestOpCmd.LISTGRAPHRES
		self.token = None
		self.gids = []
		self.adnames = []

	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpListGraphRes()
		cmd.token = d['token']
		cmd.gids  = d['gids']
		cmd.gids  = d['adnames']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpListGraphRes.from_dict(json.loads(jd))