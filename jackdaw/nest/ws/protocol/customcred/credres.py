
import json

from jackdaw.utils.encoder import UniversalEncoder 
from jackdaw.nest.ws.protocol.cmdtypes import NestOpCmd

class NestOpCredRes:
	def __init__(self):
		self.cmd = NestOpCmd.CREDRES
		self.token = None
		self.cid = None
		self.adid = None
		self.domain = None
		self.username = None
		self.secret = None
		self.stype = None
		self.description = None
	
	def to_credline(self):
		return '%s\\%s %s %s' % (self.domain, self.username, self.stype, self.secret)
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpCredRes()
		cmd.token = d['token']
		cmd.cid = d['cid']
		cmd.adid = d['adid']
		cmd.domain = d['domain']
		cmd.username = d['username']
		cmd.secret = d['secret']
		cmd.stype = d['stype']
		cmd.description = d['description']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpCredRes.from_dict(json.loads(jd))

