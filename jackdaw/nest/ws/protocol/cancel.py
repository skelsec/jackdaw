import json

from jackdaw.utils.encoder import UniversalEncoder 
from jackdaw.nest.ws.protocol.cmdtypes import NestOpCmd


class NestOpCancel:
	def __init__(self, token = None, agent_id = None):
		self.cmd = NestOpCmd.CANCEL
		self.token = token
		self.agent_id = agent_id
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpCancel()
		cmd.token = d['token']
		cmd.agent_id = d['agent_id']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpCancel.from_dict(json.loads(jd))

