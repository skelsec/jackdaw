from . import Basemodel
import datetime
from sqlalchemy import Column, Integer, String, DateTime

class LocalGroup(Basemodel):
	__tablename__ = 'localgroup'
	
	id = Column(Integer, primary_key=True)
	fetched_at = Column(DateTime, default=datetime.datetime.utcnow)
	machine_id = Column(Integer)
	ip = Column(String, index=True)
	rdns = Column(String, index=True)
	hostname = Column(String, index=True)
	sid = Column(String, index=True)
	sidusage = Column(String, index=True)
	domain = Column(String, index=True)
	username = Column(String, index=True)
	groupname = Column(String, index=True)