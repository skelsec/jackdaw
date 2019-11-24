from . import Basemodel
import datetime
from sqlalchemy import Column, Integer, String, DateTime

class NetDir(Basemodel):
	__tablename__ = 'netdir'
	
	id = Column(Integer, primary_key=True)
	fetched_at = Column(DateTime, default=datetime.datetime.utcnow)
	share_id = Column(Integer, index=True)
	parent_id = Column(Integer, index=True)
	creation_time = Column(DateTime)
	last_access_time = Column(DateTime)
	last_write_time = Column(DateTime)
	change_time = Column(DateTime)
	unc = Column(String, index=True)
	name = Column(String, index=True)

	def to_dict(self):
		return {
			'id' : self.id , 
			'fetched_at' : self.fetched_at , 
			'share_id' : self.share_id , 
			'parent_id' : self.parent_id , 
			'creation_time' : self.creation_time , 
			'last_access_time' : self.last_access_time , 
			'last_write_time' : self.last_write_time , 
			'change_time' : self.change_time , 
			'unc' : self.unc ,
			'name' : self.name ,
		}