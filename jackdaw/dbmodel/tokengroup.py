from . import Basemodel
import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey

class JackDawTokenGroup(Basemodel):
	__tablename__ = 'tokengroup'
	
	id = Column(Integer, primary_key=True)
	ad_id = Column(Integer, ForeignKey('ads.id'))
	ad = relationship("JackDawADInfo", back_populates="group_lookups")
	fetched_at = Column(DateTime, default=datetime.datetime.utcnow)
	cn = Column(String, index=True)
	dn = Column(String, index=True)
	guid = Column(String, index=True)
	sid = Column(String, index=True)
	member_sid = Column(String, index=True)
