from . import Basemodel
from sqlalchemy import Column, Integer, String, DateTime
from jackdaw.dbmodel.utils.serializer import Serializer

class SMBFile(Basemodel, Serializer):
	__tablename__ = 'smbfile'
	
	id = Column(Integer, primary_key=True)
	ad_id = Column(Integer, index=True)
	machine_sid = Column(String, index=True)
	unc = Column(String, index=True)
	size = Column(Integer, index=True)
	size_ext = Column(Integer, index=True)
	creation_time = Column(DateTime)
	last_access_time = Column(DateTime)
	last_write_time = Column(DateTime)
	change_time = Column(DateTime)
	sddl = Column(Integer, index=True)

	def to_dict(self):
		return {
			'id' : self.id,
			'ad_id' : self.ad_id ,
			'machine_sid' : self.machine_sid ,
			'unc' : self.unc ,
			'size' : self.size ,
			'size_ext' : self.size_ext ,
			'creation_time' : self.creation_time , 
			'last_access_time' : self.last_access_time , 
			'last_write_time' : self.last_write_time , 
			'change_time' : self.change_time , 
			'sddl' : self.sddl,
		}