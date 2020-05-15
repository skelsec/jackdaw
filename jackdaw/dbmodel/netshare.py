from . import Basemodel
import datetime
from sqlalchemy import Column, Integer, String, DateTime

class NetShare(Basemodel):
	__tablename__ = 'netshare'
	
	id = Column(Integer, primary_key=True)
	ad_id = Column(Integer, index=True)
	machine_sid = Column(String, index=True)
	ip = Column(String, index=True)
	rdns = Column(String, index=True)
	netname = Column(String, index=True)
	type = Column(String, index=True)
	remark = Column(String, index=True)
	passwd = Column(String, index=True)

	def to_dict(self):
		return {
			'id' : self.id , 
			'machine_id' : self.machine_id , 
			'ip' : self.ip , 
			'rdns' : self.rdns , 
			'netname' : self.netname , 
			'type' : self.type , 
			'remark' : self.remark , 
			'passwd' : self.passwd ,
		}
	