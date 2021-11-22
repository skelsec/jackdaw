import json

from jackdaw.utils.encoder import UniversalEncoder 
from jackdaw.nest.ws.protocol.cmdtypes import NestOpCmd
from jackdaw.nest.ws.protocol.credsdef import NestOpCredsDef
from jackdaw.nest.ws.protocol.targetdef import NestOpTargetDef

class NestOpGather:
	def __init__(self):
		self.cmd = NestOpCmd.GATHER
		self.token = None
		self.ldap_creds:NestOpCredsDef = None
		self.ldap_target:NestOpTargetDef = None
		self.smb_creds:NestOpCredsDef = None
		self.smb_target:NestOpTargetDef = None
		self.kerberos_creds:NestOpCredsDef = None
		self.kerberos_target:NestOpTargetDef = None
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
		cmd.ldap_creds = NestOpCredsDef.from_dict(d['ldap_creds'])
		cmd.ldap_target = NestOpTargetDef.from_dict(d['ldap_target'])

		cmd.smb_creds = NestOpCredsDef.from_dict(d['smb_creds'])
		cmd.smb_target = NestOpTargetDef.from_dict(d['smb_target'])

		if 'kerberos_creds' in d and d['kerberos_creds'] is not None:
			cmd.kerberos_creds = NestOpCredsDef.from_dict(d['kerberos_creds'])
			cmd.kerberos_target = NestOpTargetDef.from_dict(d['kerberos_target'])

		cmd.agent_id = d['agent_id']
		if cmd.agent_id is None:
			raise Exception('Agent ID must be provided for GATHER')
		
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


