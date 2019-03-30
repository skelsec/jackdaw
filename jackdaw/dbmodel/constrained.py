from . import Basemodel, lf
import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, ForeignKey

class JackDawMachineConstrainedDelegation(Basemodel):
	__tablename__ = 'constrainedmachine'

	id = Column(Integer, primary_key=True)
	machine_id = Column(Integer, ForeignKey('machines.id'))
	machine = relationship("JackDawADMachine", back_populates="allowedtodelegateto", lazy = True)
	spn = Column(String, index=True)
	targetaccount = Column(String, index=True)


class JackDawUserConstrainedDelegation(Basemodel):
	__tablename__ = 'constraineduser'

	id = Column(Integer, primary_key=True)
	user_id = Column(Integer, ForeignKey('users.id'))
	user = relationship("JackDawADUser", back_populates="allowedtodelegateto", lazy = True)
	spn = Column(String, index=True)
	targetaccount = Column(String, index=True)