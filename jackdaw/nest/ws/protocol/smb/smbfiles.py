import json

from jackdaw.utils.encoder import UniversalEncoder 
from jackdaw.nest.ws.protocol.cmdtypes import NestOpCmd
from jackdaw.nest.ws.protocol.credsdef import NestOpCredsDef
from jackdaw.nest.ws.protocol.targetdef import NestOpTargetDef

class NestOpCredsDef:
	def __init__(self):
		self.user_ad_id = None
		self.user_sid = None
		self.username = None
		self.domain = None
		self.password = None
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)

	@staticmethod
	def from_dict(d):
		cmd = NestOpCredsDef()
		cmd.username = d['username']
		cmd.domain = d['domain']
		cmd.password = d['password']
		cmd.user_ad_id = d['user_ad_id']
		cmd.user_sid = d['user_sid']
		return cmd
			
	@staticmethod
	def from_json(jd):
		return NestOpCredsDef.from_dict(json.loads(jd))

class NestOpTargetDef:
	def __init__(self):
		self.hostname = None
		self.ip = None
		self.machine_ad_id = None
		self.machine_sid = None

	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpTargetDef()
		cmd.hostname = d['hostname']
		cmd.ip = d['ip']
		cmd.machine_ad_id = d['machine_ad_id']
		cmd.machine_sid = d['machine_sid']
		return cmd

	
	@staticmethod
	def from_json(jd):
		return NestOpTargetDef.from_dict(json.loads(jd))


class NestOpSMBFiles:
	def __init__(self):
		self.cmd = NestOpCmd.SMBFILES
		self.token = None
		self.agent_id = None
		self.target = None
		self.creds = None		
		self.depth = 3

	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpSMBFiles()
		cmd.token = d['token']
		cmd.agent_id = d['agent_id']
		cmd.target = NestOpTargetDef.from_dict(d['target'])
		cmd.creds = NestOpCredsDef.from_dict(d['creds'])
		cmd.depth = d['depth']		
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpSMBFiles.from_dict(json.loads(jd))
