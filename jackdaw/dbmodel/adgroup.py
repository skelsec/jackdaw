from . import Basemodel, lf
import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey

class JackDawADGroup(Basemodel):
	__tablename__ = 'groups'
	
	id = Column(Integer, primary_key=True)
	ad_id = Column(Integer, ForeignKey('ads.id'))
	ad = relationship("JackDawADInfo", back_populates="groups", lazy = True)
	fetched_at = Column(DateTime, default=datetime.datetime.utcnow)
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
	sAMAccountType = Column(String, index=True)	
	systemFlags = Column(String, index=True)	
	whenChanged = Column(String, index=True)	
	whenCreated = Column(String, index=True)

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
		group.cn = lf(d.get('cn'))
		group.dn = lf(d.get('distinguishedName'))
		group.guid = lf(d.get('objectGUID'))
		group.sid = lf(d.get('objectSid'))
		group.description = lf(d.get('description'))
		group.grouptype = lf(d.get('groupType'))
		group.instanceType = lf(d.get('instanceType'))
		group.name = lf(d.get('name'))
		group.member = lf(d.get('member'))
		group.sAMAccountName = lf(d.get('sAMAccountName'))
		group.sAMAccountType = lf(d.get('sAMAccountType'))
		group.systemFlags = lf(d.get('systemFlags'))
		group.whenChanged = lf(d.get('whenChanged'))
		group.whenCreated = lf(d.get('whenCreated'))
		return group