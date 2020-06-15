from . import Basemodel
import datetime
from sqlalchemy import Column, Integer, String, DateTime
from jackdaw.dbmodel.utils.serializer import Serializer


class NetShare(Basemodel, Serializer):
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
			'machine_sid' : self.machine_sid , 
			'ip' : self.ip , 
			'rdns' : self.rdns , 
			'netname' : self.netname , 
			'type' : self.type , 
			'remark' : self.remark , 
			'passwd' : self.passwd ,
		}
	