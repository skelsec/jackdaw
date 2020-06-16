from . import Basemodel
import datetime
from sqlalchemy import Column, Integer, String, DateTime
from jackdaw.dbmodel.utils.serializer import Serializer

class NetError(Basemodel, Serializer):
	__tablename__ = 'neterror'
	
	id = Column(Integer, primary_key=True)
	fetched_at = Column(DateTime, default=datetime.datetime.utcnow)
	ad_id = Column(Integer, index=True)
	machine_sid = Column(String, index=True)
	error_type = Column(String, index=True)
	error = Column(String, index=True)