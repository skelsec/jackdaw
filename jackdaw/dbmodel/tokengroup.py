from . import Basemodel
import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
import json

class JackDawTokenGroup(Basemodel):
	__tablename__ = 'tokengroup'
	
	id = Column(Integer, primary_key=True)
	ad_id = Column(Integer, ForeignKey('ads.id'))
	ad = relationship("JackDawADInfo", back_populates="group_lookups", lazy = True)
	fetched_at = Column(DateTime, default=datetime.datetime.utcnow)
	cn = Column(String, index=True)
	dn = Column(String, index=True)
	guid = Column(String, index=True)
	sid = Column(String, index=True)
	member_sid = Column(String, index=True)
	objtype = Column(String)
	

	@staticmethod
	def from_dict(d):
		t = JackDawTokenGroup()
		t.ad_id = d['ad_id']
		t.fetched_at = datetime.datetime.fromisoformat(d['fetched_at'])
		t.cn = d['cn']
		t.dn = d['dn']
		t.guid = d['guid']
		t.sid = d['sid']
		t.member_sid = d['member_sid']
		t.objtype = d['objtype']
		return t

	@staticmethod
	def from_json(x):
		return JackDawTokenGroup.from_dict(json.loads(x))

	def to_dict(self):
		return {
			'ad_id' : self.ad_id,
			'fetched_at' : self.fetched_at.isoformat() if self.fetched_at is not None else datetime.datetime.utcnow().isoformat(),
			'cn' : self.cn,
			'dn' : self.dn,
			'guid' : self.guid,
			'sid' : self.sid,
			'member_sid' : self.member_sid,
			'objtype' : self.objtype
		}

	def to_json(self):
		return json.dumps(self.to_dict())