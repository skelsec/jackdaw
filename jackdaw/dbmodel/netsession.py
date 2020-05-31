from . import Basemodel
import datetime
from sqlalchemy import Column, Integer, String, DateTime
from jackdaw.dbmodel.utils.serializer import Serializer


class NetSession(Basemodel, Serializer):
	__tablename__ = 'netsession'
	
	id = Column(Integer, primary_key=True)
	ad_id = Column(Integer, index=True)
	machine_sid = Column(String, index=True)
	source = Column(String, index=True)
	ip = Column(String, index=True)
	rdns = Column(String, index=True)
	username = Column(String, index=True)
	
