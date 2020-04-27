#!/usr/bin/env python3
#
# Author:
#  Tamas Jos (@skelsec)
#

from . import Basemodel, lf
import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from jackdaw._version import __version__

class JackDawADInfo(Basemodel):
	__tablename__ = 'ads'
	
	id = Column(Integer, primary_key=True)
	fetched_at = Column(DateTime, default=datetime.datetime.utcnow)
	auditingPolicy = Column(String)
	creationTime = Column(DateTime)
	dc = Column(String)
	distinguishedName = Column(String)
	forceLogoff = Column(Integer)
	instanceType = Column(Integer)
	lockoutDuration = Column(Integer)
	lockOutObservationWindow = Column(Integer)
	lockoutThreshold = Column(Integer)
	masteredBy = Column(String)
	maxPwdAge = Column(Integer)
	minPwdAge = Column(Integer)
	minPwdLength = Column(Integer)
	name = Column(String)
	nextRid = Column(Integer)
	nTSecurityDescriptor = Column(String)
	objectCategory = Column(String)
	objectClass = Column(String)
	objectGUID = Column(String)
	objectSid = Column(String)
	pwdHistoryLength = Column(Integer)
	pwdProperties = Column(Integer)
	serverState = Column(Integer)
	systemFlags = Column(Integer)
	uASCompat = Column(Integer)
	uSNChanged = Column(Integer)
	uSNCreated = Column(Integer)
	whenChanged = Column(DateTime)
	whenCreated = Column(DateTime)
	jdversion = Column(String)
	ldap_enumeration_state = Column(String)
	smb_enumeration_state = Column(String)

	users = relationship("JackDawADUser", back_populates="ad", lazy = True)
	computers = relationship("JackDawADMachine", back_populates="ad", lazy = True)
	groups = relationship("JackDawADGroup", back_populates="ad", lazy = True)
	group_lookups = relationship("JackDawTokenGroup", back_populates="ad", lazy = True)
	spnservices = relationship("JackDawSPNService", back_populates="ad", lazy = True)
	#objectacls = relationship("JackDawADDACL", back_populates="ad", lazy='dynamic')
	customrelations = relationship("JackDawCustomRelations", back_populates="ad", lazy = True)
	ous = relationship("JackDawADOU", back_populates="ad", lazy = True)
	gpos = relationship("JackDawADGPO", back_populates="ad", lazy = True)
	sds = relationship("JackDawSD", back_populates="ad", lazy = True)
	trusts = relationship("JackDawADTrust", back_populates="ad", lazy = True)
	
	def to_dict(self):
		return {
			'id' : self.id ,
			'fetched_at' : self.fetched_at ,
			'creationTime' : self.creationTime ,
			'distinguishedName' : self.distinguishedName ,
			'forceLogoff' : self.forceLogoff ,
			'lockoutDuration' : self.lockoutDuration ,
			'lockOutObservationWindow' : self.lockOutObservationWindow ,
			'lockoutThreshold' : self.lockoutThreshold ,
			'masteredBy' : self.masteredBy ,
			'maxPwdAge' : self.maxPwdAge ,
			'minPwdAge' : self.minPwdAge ,
			'minPwdLength' : self.minPwdLength ,
			'name' : self.name ,
			'pwdHistoryLength' : self.pwdHistoryLength ,
			'pwdProperties' : self.pwdProperties ,
			'whenChanged' : self.whenChanged ,
			'whenCreated' : self.whenCreated ,
			'jdversion' : self.jdversion,
		}

	@staticmethod
	def from_dict(d):
		adinfo = JackDawADInfo()
		adinfo.auditingPolicy = lf(d.get('auditingPolicy'))
		adinfo.creationTime = lf(d.get('creationTime'))
		adinfo.dc = lf(d.get('dc'))
		adinfo.distinguishedName = lf(d.get('distinguishedName'))
		adinfo.forceLogoff = lf(d.get('forceLogoff'))
		adinfo.instanceType = lf(d.get('instanceType'))
		adinfo.lockoutDuration = lf(d.get('lockoutDuration'))
		adinfo.lockOutObservationWindow = lf(d.get('lockOutObservationWindow'))
		adinfo.lockoutThreshold = lf(d.get('lockoutThreshold'))
		adinfo.masteredBy = lf(d.get('masteredBy'))
		adinfo.maxPwdAge = lf(d.get('maxPwdAge'))
		adinfo.minPwdAge = lf(d.get('minPwdAge'))
		adinfo.minPwdLength = lf(d.get('minPwdLength'))
		adinfo.name = lf(d.get('name'))
		adinfo.nextRid = lf(d.get('nextRid'))
		adinfo.nTSecurityDescriptor = lf(d.get('nTSecurityDescriptor'))
		adinfo.objectCategory = lf(d.get('objectCategory'))
		adinfo.objectClass = lf(d.get('objectClass'))
		adinfo.objectGUID = lf(d.get('objectGUID'))
		adinfo.objectSid = lf(d.get('objectSid'))
		adinfo.pwdHistoryLength = lf(d.get('pwdHistoryLength'))
		adinfo.pwdProperties = lf(d.get('pwdProperties'))
		adinfo.serverState = lf(d.get('serverState'))
		adinfo.systemFlags = lf(d.get('systemFlags'))
		adinfo.uASCompat = lf(d.get('uASCompat'))
		adinfo.uSNChanged = lf(d.get('uSNChanged'))
		adinfo.uSNCreated = lf(d.get('uSNCreated'))
		adinfo.whenChanged = lf(d.get('whenChanged'))
		adinfo.whenCreated = lf(d.get('whenCreated'))
		if d.get('jdversion') is None:
			adinfo.jdversion = __version__
		return adinfo