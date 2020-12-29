import json

from jackdaw.utils.encoder import UniversalEncoder 
from jackdaw.nest.ws.protocol.cmdtypes import NestOpCmd


class NestOpSMBSessions:
	def __init__(self):
		self.cmd = NestOpCmd.SMBSESSIONS
		self.token = None
		self.smb_url = None
		self.all_hosts = False
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpSMBSessions()
		cmd.token = d['token']
		cmd.smb_url = d['smb_url']
		if 'all_hosts' in d:
			cmd.all_hosts = d['all_hosts']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpSMBSessions.from_dict(json.loads(jd))
