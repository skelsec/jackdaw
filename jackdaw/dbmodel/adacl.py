from . import Basemodel
import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey

class JackDawADACL(Basemodel):
	__tablename__ = 'adacl'
	
	id = Column(Integer, primary_key=True)
	ad_id = Column(Integer, ForeignKey('ads.id'))
	ad = relationship("JackDawADInfo", back_populates="objectacls", lazy = True)
	
	fetched_at = Column(DateTime, default=datetime.datetime.utcnow)
	guid = Column(String, index=True)
	sid = Column(String, index=True)
	
	cn = Column(String, index=True)
	dn = Column(String, index=True)
	
	sd_control = Column(String, index=True)
	ace_type = Column(String, index=True)
	ace_mask = Column(String, index=True)
	ace_objecttype = Column(String, index=True)
	ace_inheritedobjecttype = Column(String, index=True)
	ace_sid = Column(String, index=True)
	ace_order = Column(Integer, index = True)