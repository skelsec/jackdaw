from . import Basemodel, lf
import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, ForeignKey
from jackdaw.dbmodel.utils.serializer import Serializer

class MachineAllowedToAct(Basemodel, Serializer):
	__tablename__ = 'admachineallowedtoact'

	id = Column(Integer, primary_key=True)
	ad_id = Column(Integer, ForeignKey('adinfo.id'))
	machine_sid = Column(String, index=True)
	target_sid = Column(String, index=True)

