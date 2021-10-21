from . import Basemodel
from sqlalchemy import Column, Integer, String
from jackdaw.dbmodel.utils.serializer import Serializer

class KerberosTicket(Basemodel, Serializer):
	__tablename__ = 'kerberosticket'
	
	id = Column(Integer, primary_key=True)
	ad_id = Column(Integer, index=True)
	type = Column(String, index=True)
	kirbi = Column(String, index=True)

	
