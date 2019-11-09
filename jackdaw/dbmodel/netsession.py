from . import Basemodel
import datetime
from sqlalchemy import Column, Integer, String, DateTime

class NetSession(Basemodel):
	__tablename__ = 'netsession'
	
	id = Column(Integer, primary_key=True)
	machine_id = Column(Integer)
	fetched_at = Column(DateTime, default=datetime.datetime.utcnow)
	source = Column(String, index=True)
	ip = Column(String, index=True)
	rdns = Column(String, index=True)
	username = Column(String, index=True)
	
