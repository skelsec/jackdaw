from . import Basemodel, lf, dt, bc
import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean

class JackDawADOU(Basemodel):
	__tablename__ = 'adou'

	id = Column(Integer, primary_key=True)
	ad_id = Column(Integer, ForeignKey('ads.id'))
	ad = relationship("JackDawADInfo", back_populates="ou", lazy = True)
	
	description = Column(String, index=True)
	dn = Column(String, index=True)
	gPLink = Column(String, index=True)
	name = Column(String, index=True)
	objectCategory = Column(String, index=True)
	objectClass = Column(String, index=True)
	objectGUID = Column(String, index=True)
	ou = Column(String, index=True)
	systemFlags = Column(Integer, index=True)
	whenChanged = Column(String, index=True)
	whenCreated = Column(String, index=True)
	
	def to_dict(self):
		return {
			'id' : self.id ,
			'ad_id' : self.ad_id ,
			'description' : self.description ,
			'guid' : self.objectGUID,
			'dn' : self.dn ,
			'name' : self.name ,
			'ou' : self.ou ,
			'whenChanged' : self.whenChanged ,
			'whenCreated' : self.whenCreated ,	
		}
	
	@staticmethod
	def from_adou(u):
		adou = JackDawADOU()
		adou.description = lf(getattr(u,'description'))
		adou.dn = lf(getattr(u,'distinguishedName'))
		adou.gPLink = lf(getattr(u,'gPLink'))
		adou.name = lf(getattr(u,'name'))
		adou.objectCategory = lf(getattr(u,'objectCategory'))
		adou.objectClass = lf(getattr(u,'objectClass'))
		adou.objectGUID = lf(getattr(u,'objectGUID'))
		adou.ou = lf(getattr(u,'ou'))
		adou.systemFlags = lf(getattr(u,'systemFlags'))
		adou.whenChanged = dt(lf(getattr(u,'whenChanged')))
		adou.whenCreated = dt(lf(getattr(u,'whenCreated')))
			
		return adou
		