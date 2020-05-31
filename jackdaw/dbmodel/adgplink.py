from . import Basemodel, lf, dt, bc
import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from jackdaw.dbmodel.utils.serializer import Serializer

class Gplink(Basemodel, Serializer):
	__tablename__ = 'adgplink'

	id = Column(Integer, primary_key=True)	
	ad_id = Column(Integer, index=True)
	ou_guid = Column(String, index=True)
	gpo_dn = Column(String, index=True)
	order = Column(Integer, index=True)
	