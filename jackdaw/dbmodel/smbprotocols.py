from . import Basemodel
import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from jackdaw.dbmodel.utils.serializer import Serializer

class SMBProtocols(Basemodel, Serializer):
	__tablename__ = 'smbprotocols'
	
	id = Column(Integer, primary_key=True)
	ad_id = Column(Integer, index=True)
	machine_sid = Column(String, index=True)
	protocol = Column(String, index=True)
	
