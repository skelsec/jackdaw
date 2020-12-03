from . import Basemodel
import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
import json
from jackdaw.dbmodel.utils.serializer import Serializer


class GraphInfo(Basemodel, Serializer):
	__tablename__ = 'graphinfo'
	
	id = Column(Integer, primary_key=True)
	fetched_at = Column(DateTime, default=datetime.datetime.utcnow)
	description = Column(String, index = True)

	def __init__(self, description = None):
		self.description = description

class GraphInfoAD(Basemodel, Serializer):
	__tablename__ = 'graphinfoads'
	
	id = Column(Integer, primary_key=True)
	fetched_at = Column(DateTime, default=datetime.datetime.utcnow)
	ad_id = Column(Integer, ForeignKey('adinfo.id'))
	graph_id = Column(Integer, ForeignKey('graphinfo.id'))

	def __init__(self, ad_id, graph_id):
		self.ad_id = ad_id
		self.graph_id = graph_id