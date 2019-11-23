from . import Basemodel, lf, dt, bc
import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean

class JackDawADGPO(Basemodel):
	__tablename__ = 'adgpo'

	id = Column(Integer, primary_key=True)
	ad_id = Column(Integer, ForeignKey('ads.id'))
	ad = relationship("JackDawADInfo", back_populates="gpos", lazy = True)
	
	name = Column(String, index=True)
	dn = Column(String, index=True)
	cn = Column(String, index=True)
	flags = Column(Integer, index=True)
	path = Column(String, index=True)
	gPCFunctionalityVersion = Column(String, index=True)	
	objectClass = Column(String, index=True)
	objectGUID = Column(String, index=True)
	systemFlags = Column(Integer, index=True)
	whenChanged = Column(String, index=True)
	whenCreated = Column(String, index=True)
	
	def to_dict(self):
		return {
			'id' : self.id ,
			'ad_id' : self.ad_id ,
			'cn' : self.cn,
			'name' : self.name ,
			'dn' : self.dn ,
			'path' : self.path,
			'guid' : self.objectGUID,
			'whenChanged' : self.whenChanged ,
			'whenCreated' : self.whenCreated ,	
		}
	
	@staticmethod
	def from_adgpo(u):
		adou = JackDawADGPO()
		adou.name = lf(getattr(u,'displayName'))
		adou.dn = lf(getattr(u,'distinguishedName'))
		adou.cn = lf(getattr(u,'cn'))
		adou.path = lf(getattr(u,'gPCFileSysPath'))
		adou.flags = lf(getattr(u,'flags'))
		adou.objectClass = lf(getattr(u,'objectClass'))
		adou.objectGUID = lf(getattr(u,'objectGUID'))
		adou.systemFlags = lf(getattr(u,'systemFlags'))
		adou.whenChanged = dt(lf(getattr(u,'whenChanged')))
		adou.whenCreated = dt(lf(getattr(u,'whenCreated')))
			
		return adou
		