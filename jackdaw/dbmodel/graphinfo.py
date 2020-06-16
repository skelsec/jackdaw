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
	ad_id = Column(Integer, ForeignKey('adinfo.id'))
	description = Column(String, index = True)
