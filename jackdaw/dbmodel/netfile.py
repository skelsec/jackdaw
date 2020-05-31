from . import Basemodel
import datetime
from sqlalchemy import Column, Integer, String, DateTime
from jackdaw.dbmodel.utils.serializer import Serializer

class NetFile(Basemodel, Serializer):
	__tablename__ = 'netfile'
	
	id = Column(Integer, primary_key=True)
	folder_id = Column(Integer, index=True)
	creation_time = Column(DateTime)
	last_access_time = Column(DateTime)
	last_write_time = Column(DateTime)
	change_time = Column(DateTime)
	unc = Column(String, index=True)
	size = Column(Integer, index=True)
	name = Column(String, index=True)
	ext = Column(String, index=True)

	def to_dict(self):
		return {
			'id' : self.id , 
			'share_id' : self.share_id , 
			'parent_id' : self.parent_id , 
			'creation_time' : self.creation_time , 
			'last_access_time' : self.last_access_time , 
			'last_write_time' : self.last_write_time , 
			'change_time' : self.change_time , 
			'unc' : self.unc ,
			'size' : self.size ,
			'name' : self.name ,
			'ext' : self.ext ,

		}