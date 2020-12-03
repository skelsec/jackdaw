from . import Basemodel
import datetime
from sqlalchemy import Column, Integer, String, DateTime
from jackdaw.dbmodel.utils.serializer import Serializer

class ADObjProps(Basemodel, Serializer):
	__tablename__ = 'adobjprops'
	
	id = Column(Integer, primary_key=True)
	graph_id = Column(Integer, index=True)
	oid = Column(String, index = True)
	prop = Column(String, index = True)
	
	def __init__(self, graphid, oid, prop):
		self.graph_id = graphid
		self.oid = oid
		self.prop = prop