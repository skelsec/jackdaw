from . import Basemodel, lf
import datetime
from sqlalchemy import Column, Integer, String

class JackDawGroupUser(Basemodel):
	__tablename__ = 'groupuser'

	id = Column(Integer, primary_key=True)
	group_osid = Column(String, index=True)
	user_osid = Column(String, index=True)
	
	
	def __init__(self, group_osid, user_osid):
		self.group_osid = group_osid
		self.user_osid = user_osid
		