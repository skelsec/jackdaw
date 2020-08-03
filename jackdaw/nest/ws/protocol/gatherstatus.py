import json

from jackdaw.utils.encoder import UniversalEncoder 
from jackdaw.nest.ws.protocol.cmdtypes import NestOpCmd


class NestOpGatherStatus:
	def __init__(self):
		self.cmd = NestOpCmd.GATHERSTATUS
		self.token = None
		self.current_progress_type = None
		self.msg_type = None
		self.adid = None
		self.domain_name = None
		self.total = None
		self.step_size = None
		self.basic_running = None
		self.basic_finished = None
		self.smb_errors = None
		self.smb_sessions = None
		self.smb_shares = None
		self.smb_groups = None

	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpGatherStatus()
		cmd.token = d['token']
		cmd.current_progress_type = d['current_progress_type']
		cmd.msg_type = d['msg_type']
		cmd.adid = d['adid']
		cmd.domain_name = d['domain_name']
		cmd.total = d['total']
		cmd.step_size = d['step_size']
		cmd.basic_running = d['basic_running']
		cmd.basic_finished = d['basic_finished']
		cmd.smb_errors = d['smb_errors']
		cmd.smb_sessions = d['smb_sessions']
		cmd.smb_shares = d['smb_shares']
		cmd.smb_groups = d['smb_groups']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpGatherStatus.from_dict(json.loads(jd))
