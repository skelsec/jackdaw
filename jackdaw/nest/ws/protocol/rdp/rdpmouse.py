import json

from jackdaw.utils.encoder import UniversalEncoder 
from jackdaw.nest.ws.protocol.cmdtypes import NestOpCmd
from jackdaw.nest.ws.protocol.credsdef import NestOpCredsDef
from jackdaw.nest.ws.protocol.targetdef import NestOpTargetDef

class NestOpRDPMouse:
	def __init__(self):
		self.cmd = NestOpCmd.RDPMOUSE
		self.token = None
		self.xPos:int = None
		self.yPos:int = None
		self.button:int = None
		self.pressed:bool = None

	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpRDPMouse()
		cmd.token = d['token']
		cmd.xPos = d['xPos']
		cmd.yPos = d['yPos']
		cmd.button = d['button']
		cmd.pressed = d['pressed']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpRDPMouse.from_dict(json.loads(jd))
