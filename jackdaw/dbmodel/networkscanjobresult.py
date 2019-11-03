from . import Basemodel
import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean

class NetworkScanJobResult(Basemodel):
	__tablename__ = 'networkscanjobresult'
	
	id = Column(Integer, primary_key=True)
	job_id = Column(Integer, ForeignKey('networkscanjob.id'))
	created_at = Column(DateTime, default=datetime.datetime.utcnow)
	is_error = Column(Boolean, index=True)
	result = Column(String, index=True)
