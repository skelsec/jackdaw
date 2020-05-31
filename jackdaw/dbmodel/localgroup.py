from . import Basemodel
import datetime
from sqlalchemy import Column, Integer, String, DateTime

from jackdaw.dbmodel.utils.serializer import Serializer

class LocalGroup(Basemodel, Serializer):
	__tablename__ = 'netlocalgroup'
	
	id = Column(Integer, primary_key=True)
	ad_id = Column(Integer, index=True)
	machine_sid = Column(String, index=True)
	ip = Column(String, index=True)
	rdns = Column(String, index=True)
	hostname = Column(String, index=True)
	sid = Column(String, index=True)
	sidusage = Column(String, index=True)
	domain = Column(String, index=True)
	username = Column(String, index=True)
	groupname = Column(String, index=True)