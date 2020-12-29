from . import Basemodel
import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from jackdaw.dbmodel.utils.serializer import Serializer


class CustomTarget(Basemodel, Serializer):
	__tablename__ = 'customtargets'
	
	id = Column(Integer, primary_key=True)
	ownerid = Column(String, index=True)
	linksid = Column(String, index=True)
	hostname = Column(String, index=True)
	description = Column(String, index=True)

	def __init__(self, hostname, description, linksid = None, ownerid=None):
		self.linksid = linksid
		self.hostname = hostname
		self.ownerid = ownerid
		self.description = description