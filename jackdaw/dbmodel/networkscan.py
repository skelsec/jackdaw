from . import Basemodel
import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean

class NetworkScan(Basemodel):
	__tablename__ = 'networkscan'
	
	id = Column(Integer, primary_key=True)
	created_at = Column(DateTime, default=datetime.datetime.utcnow)

	
	targets = relationship("NetworkScanTarget", back_populates="scan", lazy = True)