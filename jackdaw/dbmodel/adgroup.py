from . import Basemodel, lf
import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from jackdaw.dbmodel.utils.serializer import Serializer

class Group(Basemodel, Serializer):
	__tablename__ = 'adgroups'
	
	id = Column(Integer, primary_key=True)
	ad_id = Column(Integer, ForeignKey('adinfo.id'))
	cn = Column(String, index=True)
	dn = Column(String, index=True)
	
	objectGUID = Column(String, index=True)
	objectSid = Column(String, index=True)
	description = Column(String, index=True)
	grouptype = Column(String, index=True)
	
	instanceType = Column(String, index=True)	
	name = Column(String, index=True)	
	member = Column(String)	
	sAMAccountName = Column(String, index=True)	
	systemFlags = Column(String, index=True)	
	whenChanged = Column(DateTime, index=True)	
	whenCreated = Column(DateTime, index=True)

	def to_dict(self):
		return {
			'id' : self.id ,
			'ad_id' : self.ad_id ,
			'sid' : self.objectSid ,
			'objectGUID' : self.objectGUID,
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
		group = Group()
		group.cn = d.get('cn')
		group.dn = d.get('distinguishedName')
		group.objectGUID = d.get('objectGUID')
		group.objectSid = d.get('objectSid')
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