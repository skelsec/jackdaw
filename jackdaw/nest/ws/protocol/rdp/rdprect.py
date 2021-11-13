import json

from jackdaw.utils.encoder import UniversalEncoder 
from jackdaw.nest.ws.protocol.cmdtypes import NestOpCmd
from jackdaw.nest.ws.protocol.credsdef import NestOpCredsDef
from jackdaw.nest.ws.protocol.targetdef import NestOpTargetDef

class NestOpRDPRectangle:
	def __init__(self):
		self.cmd = NestOpCmd.RDPRECT
		self.token = None
		self.x = None #start X
		self.y = None # start Y
		self.image = None #image base64 data
		self.width = None #image width
		self.height = None # image height
		self.imgtype = None #image type (PNG)

	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpRDPRectangle()
		cmd.token = d['token']
		cmd.x = int(d['x'])
		cmd.y = int(d['y'])
		cmd.image = d['image']
		cmd.width = int(d['width'])
		cmd.height = int(d['height'])
		cmd.imgtype = d['imgtype']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpRDPRectangle.from_dict(json.loads(jd))
