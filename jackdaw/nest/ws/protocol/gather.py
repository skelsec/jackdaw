import json

from jackdaw.utils.encoder import UniversalEncoder 
from jackdaw.nest.ws.protocol.cmdtypes import NestOpCmd


class NestOpGather:
	def __init__(self):
		self.cmd = NestOpCmd.GATHER
		self.token = None
		self.ldap_url = None
		self.smb_url = None
		self.kerberos_url = None
		self.ldap_workers = 4
		self.smb_worker_cnt = 500
		self.dns = None
		self.stream_data = False
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpGather()
		cmd.token = d['token']
		cmd.ldap_url = d['ldap_url']
		cmd.smb_url = d['smb_url']
		cmd.kerberos_url = d['kerberos_url']
		if 'ldap_workers' in d:
			cmd.exclude = d['ldap_workers']
		if 'smb_worker_cnt' in d:
			cmd.exclude = d['smb_worker_cnt']
		if 'dns' in d:
			cmd.exclude = d['dns']
		if 'stream_data' in d:
			cmd.stream_data = d['stream_data']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpGather.from_dict(json.loads(jd))

