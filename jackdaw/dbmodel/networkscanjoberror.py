from . import Basemodel
import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean

class NetworkScanJobError(Basemodel):
	__tablename__ = 'networkscanjoberror'
	
	id = Column(Integer, primary_key=True)
	job_id = Column(Integer, ForeignKey('networkscanjob.id'))
	created_at = Column(DateTime, default=datetime.datetime.utcnow)
	error = Column(String, index=True)


	