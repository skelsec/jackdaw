from . import Basemodel, lf
import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey

class JackDawADGroup(Basemodel):
	__tablename__ = 'groups'
	
	id = Column(Integer, primary_key=True)
	ad_id = Column(Integer, ForeignKey('ads.id'))
	ad = relationship("JackDawADInfo", back_populates="groups", lazy = True)
	cn = Column(String, index=True)
	dn = Column(String, index=True)
	
	guid = Column(String, index=True)
	sid = Column(String, index=True)
	description = Column(String, index=True)
	grouptype = Column(String, index=True)
	
	instanceType = Column(String, index=True)	
	name = Column(String, index=True)	
	member = Column(String, index=True)	
	sAMAccountName = Column(String, index=True)	
	systemFlags = Column(String, index=True)	
	whenChanged = Column(DateTime, index=True)	
	whenCreated = Column(DateTime, index=True)

	def to_dict(self):
		return {
			'id' : self.id ,
			'ad_id' : self.ad_id ,
			'sid' : self.sid ,
			'description' : self.description ,
			'grouptype' : self.grouptype ,
			'name' : self.name ,
			'member' : self.member ,
			'sAMAccountName' : self.sAMAccountName ,
			'systemFlags' : self.systemFlags ,
			'whenChanged' : self.whenChanged ,
			'whenCreated' : self.whenCreated ,
		}

	@staticmethod
	def from_dict(d):
		group = JackDawADGroup()
		group.cn = d.get('cn')
		group.dn = d.get('distinguishedName')
		group.guid = d.get('objectGUID')
		group.sid = d.get('objectSid')
		group.description = d.get('description')
		group.grouptype = d.get('groupType')
		group.instanceType = d.get('instanceType')
		group.name = d.get('name')
		group.member = lf(d.get('member'))
		group.sAMAccountName = d.get('sAMAccountName')
		group.systemFlags = d.get('systemFlags')
		group.whenChanged = d.get('whenChanged')
		group.whenCreated = d.get('whenCreated')
		return group