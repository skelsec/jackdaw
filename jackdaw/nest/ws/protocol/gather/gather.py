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
		self.agent_id = None
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpGather()
		cmd.token = d['token']
		cmd.ldap_url = d['ldap_url']
		cmd.agent_id = d['agent_id']
		if cmd.agent_id is None:
			raise Exception('Agent ID must be provided for GATHER')
		if cmd.ldap_url.upper() == 'AUTO':
			cmd.ldap_url = 'auto'
		cmd.smb_url = d['smb_url']
		if cmd.smb_url.upper() == 'AUTO':
			cmd.smb_url = 'auto'
		cmd.kerberos_url = d['kerberos_url']
		if cmd.kerberos_url.upper() == 'AUTO':
			cmd.kerberos_url = 'auto'
		if 'ldap_workers' in d:
			cmd.ldap_workers = d['ldap_workers']
		if 'smb_worker_cnt' in d:
			cmd.smb_worker_cnt = d['smb_worker_cnt']
		if 'dns' in d:
			cmd.dns = d['dns']
			if cmd.dns is not None:
				if cmd.dns.upper() == 'AUTO':
					cmd.dns = 'auto'
		if 'stream_data' in d:
			cmd.stream_data = d['stream_data']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpGather.from_dict(json.loads(jd))


class NestOpGroupBuffRes:
	def __init__(self):
		self.cmd = NestOpCmd.GROUPBUFFRES
		self.token = None
		self.groups = []
	
	def to_dict(self):
		return {
			'cmd' : self.cmd.value,
			'token' : self.token,
			'groups' : [groups.to_dict() for groups in self.groups],
		}
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpGroupBuffRes()
		cmd.token = d['token']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpGroupBuffRes.from_dict(json.loads(jd))


