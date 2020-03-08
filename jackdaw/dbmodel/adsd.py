
from . import Basemodel
import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean


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