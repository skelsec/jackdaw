
from . import Basemodel
import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
import json

class JackDawSD(Basemodel):
	__tablename__ = 'adsd'
	
	id = Column(Integer, primary_key=True)
	ad_id = Column(Integer, ForeignKey('ads.id'))
	ad = relationship("JackDawADInfo", back_populates="sds", lazy = True)
	
	fetched_at = Column(DateTime, default=datetime.datetime.utcnow)
	guid = Column(String, index=True)
	sid = Column(String, index=True)
	object_type = Column(String, index=True)
	sd = Column(String, index=True)


	@staticmethod
	def from_dict(d):
		t = JackDawSD()
		t.ad_id = d['ad_id']
		t.fetched_at = datetime.datetime.fromisoformat(d['fetched_at'])
		t.guid = d['guid']
		t.sid = d['sid']
		t.object_type = d['object_type']
		t.sd = d['sd']
		return t

	@staticmethod
	def from_json(x):
		return JackDawSD.from_dict(json.loads(x))

	def to_dict(self):
		return {
			'ad_id' : self.ad_id,
			'fetched_at' : self.fetched_at.isoformat() if self.fetched_at is not None else datetime.datetime.utcnow().isoformat(),
			'guid' : self.guid,
			'sid' : self.sid,
			'object_type' : self.object_type,
			'sd' : self.sd
		}

	def to_json(self):
		return json.dumps(self.to_dict())