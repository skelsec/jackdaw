from . import Basemodel
from sqlalchemy import Column, Integer, String
from jackdaw.dbmodel.utils.serializer import Serializer
from sqlalchemy import Index, func


class RegSession(Basemodel, Serializer):
	__tablename__ = 'regsession'
	
	id = Column(Integer, primary_key=True)
	ad_id = Column(Integer, index=True)
	machine_sid = Column(String, index=True)
	source = Column(String, index=True)
	user_sid = Column(String, index=True)
	
	Index('regsessionlower', func.lower(source))