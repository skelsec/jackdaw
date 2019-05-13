from . import Basemodel, lf
import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, ForeignKey

class JackDawMachineConstrainedDelegation(Basemodel):
	__tablename__ = 'constrainedmachine'

	id = Column(Integer, primary_key=True)
	ad_id = Column(Integer, ForeignKey('ads.id'))
	sid = Column(String, index=True)
	spn = Column(String, index=True)
	targetaccount = Column(String, index=True)
