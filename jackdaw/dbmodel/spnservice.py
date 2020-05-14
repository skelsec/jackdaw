from . import Basemodel
import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey

class JackDawSPNService(Basemodel):
	__tablename__ = 'spnservice'
	
	id = Column(Integer, primary_key=True)
	ad_id = Column(Integer, ForeignKey('ads.id'))
	ad = relationship("JackDawADInfo", back_populates="spnservices", lazy = True)
	owner_sid = Column(String, index=True)
	service_class = Column(String, index=True)
	computername = Column(String, index=True)
	port = Column(Integer, index=True)
	service_name = Column(String, index=True)
	