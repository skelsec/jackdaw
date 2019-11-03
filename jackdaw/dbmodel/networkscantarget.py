from . import Basemodel
import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean

class NetworkScanTarget(Basemodel):
	__tablename__ = 'networkscantarget'
	
	id = Column(Integer, primary_key=True)
	scan_id = Column(Integer, ForeignKey('networkscan.id'))
	created_at = Column(DateTime, default=datetime.datetime.utcnow)
	address = Column(String, index=True)
	protocol = Column(String, index=True)
	port = Column(String, index=True)

	scan = relationship("NetworkScan", back_populates="targets", lazy = True)
	jobs = relationship("NetworkScanJob", back_populates="target", lazy = True)
