
from . import Basemodel
import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
import json
from jackdaw.dbmodel.utils.serializer import Serializer

class JackDawSD(Basemodel, Serializer):
	__tablename__ = 'adsds'
	
	id = Column(Integer, primary_key=True)
	ad_id = Column(Integer, ForeignKey('adinfo.id'))
	
	guid = Column(String, index=True)
	sid = Column(String, index=True)
	object_type = Column(String, index=True)
	sd_hash = Column(String, index=True)
	sd = Column(String)


	@staticmethod
	def from_dict(d):
		t = JackDawSD()
		t.ad_id = d['ad_id']
		t.guid = d['guid']
		t.sid = d['sid']
		t.object_type = d['object_type']
		t.sd = d['sd']
		t.sd_hash = d['sd_hash']
		return t

	@staticmethod
	def from_json(x):
		return JackDawSD.from_dict(json.loads(x))

	def to_dict(self):
		return {
			'ad_id' : self.ad_id,
			'guid' : self.guid,
			'sid' : self.sid,
			'object_type' : self.object_type,
			'sd' : self.sd,
			'sd_hash' : self.sd_hash
		}

	def to_json(self):
		return json.dumps(self.to_dict())