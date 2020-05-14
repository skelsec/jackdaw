from . import Basemodel
import datetime
from sqlalchemy import Column, Integer, String, DateTime

class NetSession(Basemodel):
	__tablename__ = 'netsession'
	
	id = Column(Integer, primary_key=True)
	machine_sid = Column(String, index=True)
	source = Column(String, index=True)
	ip = Column(String, index=True)
	rdns = Column(String, index=True)
	username = Column(String, index=True)
	
