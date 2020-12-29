from . import Basemodel
import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from jackdaw.dbmodel.utils.serializer import Serializer


class PortalUser(Basemodel, Serializer):
	__tablename__ = 'portaluser'
	
	id = Column(Integer, primary_key=True)
	username = Column(String)
	password = Column(String)
	isadmin = Column(Boolean)