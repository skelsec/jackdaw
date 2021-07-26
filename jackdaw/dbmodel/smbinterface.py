from . import Basemodel
import datetime
from sqlalchemy import Column, Integer, String, DateTime
from jackdaw.dbmodel.utils.serializer import Serializer
from sqlalchemy import Index, func


class SMBInterface(Basemodel, Serializer):
	__tablename__ = 'smbinterface'
	
	id = Column(Integer, primary_key=True)
	ad_id = Column(Integer, index=True)
	machine_sid = Column(String, index=True)
	address = Column(String, index=True)
	