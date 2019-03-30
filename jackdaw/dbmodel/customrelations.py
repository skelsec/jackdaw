from . import Basemodel
import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean

class JackDawCustomRelations(Basemodel):
	"""
	This table filled manually by the user(s), and is used to add additional relations between arbitrary nodes (be that user, group, machine etc), ones that could not be determined programmatically
	Data here will be used in node2node path calculations
	"""
	__tablename__ = 'customrelations'
	
	id = Column(Integer, primary_key=True)
	ad_id = Column(Integer, ForeignKey('ads.id'))
	ad = relationship("JackDawADInfo", back_populates="customrelations", lazy = True)
	created_at = Column(DateTime, default=datetime.datetime.utcnow)
	sid = Column(String, index=True)
	target_sid = Column(String, index=True)