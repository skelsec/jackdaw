from . import Basemodel
import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from jackdaw.dbmodel.utils.serializer import Serializer


class SPNService(Basemodel, Serializer):
	__tablename__ = 'adspnservices'
	
	id = Column(Integer, primary_key=True)
	ad_id = Column(Integer, ForeignKey('adinfo.id'))
	owner_sid = Column(String, index=True)
	service_class = Column(String, index=True)
	computername = Column(String, index=True)
	port = Column(String, index=True)
	service_name = Column(String, index=True)
	