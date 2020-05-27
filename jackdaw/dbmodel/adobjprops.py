from . import Basemodel
import datetime
from sqlalchemy import Column, Integer, String, DateTime

class JackDawADObjProps(Basemodel):
	__tablename__ = 'adobjprops'
	
	id = Column(Integer, primary_key=True)
	ad_id = Column(Integer, index=True)
	oid = Column(String, index = True)
	prop = Column(String, index = True)
	