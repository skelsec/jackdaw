from . import Basemodel
import datetime
from sqlalchemy import Column, Integer, String, DateTime

class NetShare(Basemodel):
	__tablename__ = 'netshare'
	
	id = Column(Integer, primary_key=True)
	fetched_at = Column(DateTime, default=datetime.datetime.utcnow)
	machine_id = Column(Integer)
	ip = Column(String, index=True)
	rdns = Column(String, index=True)
	netname = Column(String, index=True)
	type = Column(String, index=True)
	remark = Column(String, index=True)
	passwd = Column(String, index=True)

	def to_dict(self):
		return {
			'id' : self.id , 
			'fetched_at' : self.fetched_at , 
			'machine_id' : self.machine_id , 
			'ip' : self.ip , 
			'rdns' : self.rdns , 
			'netname' : self.netname , 
			'type' : self.type , 
			'remark' : self.remark , 
			'passwd' : self.passwd ,
		}
	