
import json

from jackdaw.utils.encoder import UniversalEncoder 
from jackdaw.nest.ws.protocol.cmdtypes import NestOpCmd

class NestOpTCPScan:
	def __init__(self):
		self.cmd = NestOpCmd.TCPSCAN
		self.token = None
		self.targets = []
		self.ports = []
		self.settings = None
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpTCPScan()
		cmd.token = d['token']
		cmd.targets = d['targets']
		cmd.ports = d['ports']
		if 'settings' in d:
			cmd.settings = d['settings']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpTCPScan.from_dict(json.loads(jd))


class NestOpTCPScanRes:
	def __init__(self):
		self.cmd = NestOpCmd.TCPSCANRES
		self.token = None
		self.host = None
		self.port = None
		self.status = None
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpTCPScanRes()
		cmd.token = d['token']
		cmd.host = d['host']
		cmd.port = d['port']
		cmd.settings = d['status']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpTCPScanRes.from_dict(json.loads(jd))