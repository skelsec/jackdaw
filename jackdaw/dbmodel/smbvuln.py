from . import Basemodel
import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from jackdaw.dbmodel.utils.serializer import Serializer

class SMBVuln(Basemodel, Serializer):
	__tablename__ = 'smbvulns'
	
	id = Column(Integer, primary_key=True)
	ad_id = Column(Integer, index=True)
	machine_sid = Column(String, index=True)
	vulnd_id = Column(String, index=True) #ANON_LOGON/MS17-010 etc
	