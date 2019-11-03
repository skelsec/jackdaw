from . import Basemodel
import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean

class NetworkScanJob(Basemodel):
	__tablename__ = 'networkscanjob'
	
	id = Column(Integer, primary_key=True)
	created_at = Column(DateTime, default=datetime.datetime.utcnow)
	target_id = Column(Integer, ForeignKey('networkscantarget.id'))
	plugin = Column(String, index=True)
	plugin_data = Column(String, index=True)


	target = relationship("NetworkScanTarget", back_populates="jobs", lazy = True)
	results = relationship("NetworkScanJobResult", back_populates="job", lazy = True)