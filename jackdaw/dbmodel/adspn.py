from . import Basemodel
import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from jackdaw.dbmodel.utils.serializer import Serializer

class JackDawSPN(Basemodel, Serializer):
	__tablename__ = 'adspn'
	
	id = Column(Integer, primary_key=True)
	ad_id = Column(Integer, ForeignKey('adinfo.id'))
	owner_sid = Column(String, index=True)
	service_class = Column(String, index=True)
	computername = Column(String, index=True)
	port = Column(String, index=True)
	service_name = Column(String, index=True)


	@staticmethod
	def from_spn_str(s, user_sid = None):
		uspn = JackDawSPN()
		port = None
		service_name = None
		service_class, t = s.split('/',1)
		m = t.find(':')
		if m != -1:
			computername, port = t.rsplit(':',1)
			if port.find('/') != -1:
				port, service_name = port.rsplit('/',1)
		else:
			computername = t
			if computername.find('/') != -1:
				computername, service_name = computername.rsplit('/',1)

		uspn.owner_sid = user_sid
		uspn.computername = computername
		uspn.service_class = service_class
		uspn.service_name = service_name
		uspn.port = port
		return uspn