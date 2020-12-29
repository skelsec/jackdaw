from . import Basemodel
import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from jackdaw.dbmodel.utils.serializer import Serializer


class StoredCred(Basemodel, Serializer):
	__tablename__ = 'storedcreds'
	
	id = Column(Integer, primary_key=True)
	ownerid = Column(String, index=True)
	domain = Column(String)
	username = Column(String)
	password = Column(String)
	description = Column(String, index=True)

	def __init__(self, username, password, description, domain = None, ownerid=None):
		self.ownerid = ownerid
		self.domain   = domain
		self.username = username
		self.password = password
		self.description = description