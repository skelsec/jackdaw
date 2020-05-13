from . import Basemodel, lf
import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, ForeignKey

class JackDawMachineConstrainedDelegation(Basemodel):
	__tablename__ = 'constrainedmachine'

	id = Column(Integer, primary_key=True)
	machine_id = Column(Integer, ForeignKey('machines.id'))
	machine = relationship("JackDawADMachine", back_populates="allowedtodelegateto", lazy = True)
	target_service = Column(String, index=True)
	target_server = Column(String, index=True)
	target_port = Column(String, index=True)

	@staticmethod
	def from_spn_str(s, machine_id = None):
		d = JackDawMachineConstrainedDelegation()
		d.machine_id = machine_id
		if s.find('/') != -1:
			d.target_service, d.target_server = s.split('/')
		else:
			d.target_server = s
		
		if d.target_server.find(':') != -1:
			d.target_server, d.target_port = d.target_server.split(':')
		
		return d




class JackDawUserConstrainedDelegation(Basemodel):
	__tablename__ = 'constraineduser'

	id = Column(Integer, primary_key=True)
	user_id = Column(Integer, ForeignKey('users.id'))
	user = relationship("JackDawADUser", back_populates="allowedtodelegateto", lazy = True)
	spn = Column(String, index=True)
	targetaccount = Column(String, index=True)