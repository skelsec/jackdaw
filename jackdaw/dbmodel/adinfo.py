#!/usr/bin/env python3
#
# Author:
#  Tamas Jos (@skelsec)
#

from . import Basemodel, lf
import datetime
import hashlib
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger, Boolean
from jackdaw._version import __version__
from jackdaw.dbmodel.utils.serializer import Serializer

class ADInfo(Basemodel, Serializer):
	__tablename__ = 'adinfo'
	
	id = Column(Integer, primary_key=True)
	fetched_at = Column(DateTime, default=datetime.datetime.utcnow)
	auditingPolicy = Column(String)
	creationTime = Column(DateTime)
	dc = Column(String)
	distinguishedName = Column(String)
	forceLogoff = Column(BigInteger)
	instanceType = Column(Integer)
	lockoutDuration = Column(BigInteger)
	lockOutObservationWindow = Column(BigInteger)
	lockoutThreshold = Column(Integer)
	masteredBy = Column(String)
	maxPwdAge = Column(BigInteger)
	minPwdAge = Column(BigInteger)
	minPwdLength = Column(Integer)
	name = Column(String)
	nextRid = Column(Integer)
	objectCategory = Column(String)
	objectClass = Column(String)
	objectGUID = Column(String)
	objectSid = Column(String)
	pwdHistoryLength = Column(Integer)
	pwdProperties = Column(Integer)
	serverState = Column(BigInteger)
	systemFlags = Column(BigInteger)
	uASCompat = Column(BigInteger)
	uSNChanged = Column(BigInteger)
	uSNCreated = Column(BigInteger)
	whenChanged = Column(DateTime)
	whenCreated = Column(DateTime)
	domainmodelevel = Column(Integer)
	jdversion = Column(String)
	ldap_enumeration_state = Column(String)
	smb_enumeration_state = Column(String)
	ldap_members_finished = Column(Boolean)
	ldap_sds_finished = Column(Boolean)
	edges_finished = Column(Boolean)

	checksum = Column(String, index = True)

	def gen_checksum(self):
		ctx = hashlib.md5()
		ctx.update(str(self.forceLogoff).encode())
		ctx.update(str(self.serverState).encode())
		ctx.update(str(self.distinguishedName).encode())
		ctx.update(str(self.whenCreated).encode())
		ctx.update(str(self.domainmodelevel).encode())
		ctx.update(str(self.systemFlags).encode())
		ctx.update(str(self.masteredBy).encode())
		ctx.update(str(self.pwdHistoryLength).encode())
		ctx.update(str(self.pwdProperties).encode())
		ctx.update(str(self.maxPwdAge).encode())
		ctx.update(str(self.minPwdAge).encode())
		ctx.update(str(self.minPwdLength).encode())
		self.checksum = ctx.hexdigest()
	
	def to_dict(self):
		return {
			'id' : self.id,
			'fetched_at' : self.fetched_at,
			'auditingPolicy' : self.auditingPolicy,
			'creationTime' : self.creationTime,
			'dc' : self.dc,
			'distinguishedName' : self.distinguishedName,
			'forceLogoff' : self.forceLogoff,
			'instanceType' : self.instanceType,
			'lockoutDuration' : self.lockoutDuration,
			'lockOutObservationWindow' : self.lockOutObservationWindow,
			'lockoutThreshold' : self.lockoutThreshold,
			'masteredBy' : self.masteredBy,
			'maxPwdAge' : self.maxPwdAge,
			'minPwdAge' : self.minPwdAge,
			'minPwdLength' : self.minPwdLength,
			'name' : self.name,
			'nextRid' : self.nextRid,
			'objectCategory' : self.objectCategory,
			'objectClass' : self.objectClass,
			'objectGUID' : self.objectGUID,
			'objectSid' : self.objectSid,
			'pwdHistoryLength' : self.pwdHistoryLength,
			'pwdProperties' : self.pwdProperties,
			'serverState' : self.serverState,
			'systemFlags' : self.systemFlags,
			'uASCompat' : self.uASCompat,
			'uSNChanged' : self.uSNChanged,
			'uSNCreated' : self.uSNCreated,
			'whenChanged' : self.whenChanged,
			'whenCreated' : self.whenCreated,
			'domainmodelevel' : self.domainmodelevel,
			'jdversion' : self.jdversion,
			'ldap_enumeration_state' : self.ldap_enumeration_state,
			'smb_enumeration_state' : self.smb_enumeration_state,
			'checksum' : self.checksum,
		}

	@staticmethod
	def from_dict(d):
		adinfo = ADInfo()
		adinfo.id = d.get('id')
		adinfo.fetched_at = d.get('fetched_at')
		adinfo.auditingPolicy = d.get('auditingPolicy')
		adinfo.creationTime = d.get('creationTime')
		adinfo.dc = d.get('dc')
		adinfo.distinguishedName = d.get('distinguishedName')
		adinfo.forceLogoff = d.get('forceLogoff')
		adinfo.instanceType = d.get('instanceType')
		adinfo.lockoutDuration = d.get('lockoutDuration')
		adinfo.lockOutObservationWindow = d.get('lockOutObservationWindow')
		adinfo.lockoutThreshold = d.get('lockoutThreshold')
		adinfo.masteredBy = d.get('masteredBy')
		adinfo.maxPwdAge = d.get('maxPwdAge')
		adinfo.minPwdAge = d.get('minPwdAge')
		adinfo.minPwdLength = d.get('minPwdLength')
		adinfo.name = d.get('name')
		adinfo.nextRid = d.get('nextRid')
		adinfo.objectCategory = d.get('objectCategory')
		adinfo.objectClass = d.get('objectClass')
		adinfo.objectGUID = d.get('objectGUID')
		adinfo.objectSid = d.get('objectSid')
		adinfo.pwdHistoryLength = d.get('pwdHistoryLength')
		adinfo.pwdProperties = d.get('pwdProperties')
		adinfo.serverState = d.get('serverState')
		adinfo.systemFlags = d.get('systemFlags')
		adinfo.uASCompat = d.get('uASCompat')
		adinfo.uSNChanged = d.get('uSNChanged')
		adinfo.uSNCreated = d.get('uSNCreated')
		adinfo.whenChanged = d.get('whenChanged')
		adinfo.whenCreated = d.get('whenCreated')
		adinfo.jdversion = d.get('jdversion')
		adinfo.ldap_enumeration_state = d.get('ldap_enumeration_state')
		adinfo.smb_enumeration_state = d.get('smb_enumeration_state')
		adinfo.domainmodelevel = d.get('domainmodelevel')
		adinfo.gen_checksum()
		return adinfo


	@staticmethod
	def from_msldap(d):
		adinfo = ADInfo()
		adinfo.auditingPolicy = d.auditingPolicy
		adinfo.creationTime = d.creationTime
		adinfo.dc = d.dc
		adinfo.distinguishedName = d.distinguishedName
		adinfo.forceLogoff = d.forceLogoff.total_seconds()
		adinfo.instanceType = d.instanceType
		adinfo.lockoutDuration = d.lockoutDuration
		adinfo.lockOutObservationWindow = d.lockOutObservationWindow
		adinfo.lockoutThreshold = d.lockoutThreshold
		adinfo.masteredBy = d.masteredBy
		adinfo.maxPwdAge = d.maxPwdAge.total_seconds()
		adinfo.minPwdAge = d.minPwdAge.total_seconds()
		adinfo.minPwdLength = d.minPwdLength
		adinfo.name = d.name
		adinfo.nextRid = d.nextRid
		adinfo.objectCategory = d.objectCategory
		adinfo.objectClass =  lf(d.objectClass)
		adinfo.objectGUID = d.objectGUID
		adinfo.objectSid = d.objectSid
		adinfo.pwdHistoryLength = d.pwdHistoryLength
		adinfo.pwdProperties = d.pwdProperties
		adinfo.serverState = d.serverState
		adinfo.systemFlags = d.systemFlags
		adinfo.uASCompat = d.uASCompat
		adinfo.uSNChanged = d.uSNChanged
		adinfo.uSNCreated = d.uSNCreated
		adinfo.domainmodelevel = d.domainmodelevel
		adinfo.whenChanged = d.whenChanged
		adinfo.whenCreated = d.whenCreated
		adinfo.jdversion = __version__
		adinfo.gen_checksum()
		return adinfo