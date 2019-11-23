from . import Basemodel, lf, dt, bc
import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean

class JackDawADGplink(Basemodel):
	__tablename__ = 'adgplink'

	id = Column(Integer, primary_key=True)	
	ent_id = Column(Integer, index=True)
	gpo_dn = Column(String, index=True)
	order = Column(Integer, index=True)
	
	def to_dict(self):
		return {
			'id' : self.id ,
			'ent_id' : self.name ,
			'gpo_dn' : self.dn ,
			'order' : self.path,
		}
	