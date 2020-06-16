from . import Basemodel, lf
import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, ForeignKey
from jackdaw.dbmodel.utils.serializer import Serializer

class MachineConstrainedDelegation(Basemodel, Serializer):
	__tablename__ = 'adconstrainedmachine'

	id = Column(Integer, primary_key=True)
	ad_id = Column(Integer, ForeignKey('adinfo.id'))
	machine_sid = Column(String, index=True)
	target_service = Column(String, index=True)
	target_server = Column(String, index=True)
	target_port = Column(String, index=True)

	@staticmethod
	def from_spn_str(s, machine_sid = None):
		d = MachineConstrainedDelegation()
		d.machine_sid = machine_sid
		if s.find('/') != -1:
			d.target_service, d.target_server = s.split('/')
		else:
			d.target_server = s
		
		if d.target_server.find(':') != -1:
			d.target_server, d.target_port = d.target_server.split(':')
		
		return d
