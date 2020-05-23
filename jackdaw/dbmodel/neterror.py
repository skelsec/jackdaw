from . import Basemodel
import datetime
from sqlalchemy import Column, Integer, String, DateTime

class NetError(Basemodel):
	__tablename__ = 'neterror'
	
	id = Column(Integer, primary_key=True)
	ad_id = Column(Integer, index=True)
	machine_sid = Column(String, index=True)
	error_type = Column(String, index=True)
	error = Column(String, index=True)