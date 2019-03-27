from . import Basemodel, lf, dt, bc
import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean

class JackDawADUser(Basemodel):
	__tablename__ = 'users'

	# Now for the attributes
	id = Column(Integer, primary_key=True)
	ad_id = Column(Integer, ForeignKey('ads.id'))
	ad = relationship("JackDawADInfo", back_populates="users")
	fetched_at = Column(DateTime, default=datetime.datetime.utcnow)
	sn = Column(String)
	cn = Column(String)
	dn = Column(String)
	initials = Column(String)
	givenName = Column(String)
	displayName = Column(String)
	name = Column(String)
	objectCategory = Column(String)
	objectClass = Column(String)
	objectGUID = Column(String)
	objectSid = Column(String, index=True)
	primaryGroupID = Column(String)
	sAMAccountName = Column(String, index=True)
	userPrincipalName = Column(String)
	servicePrincipalName = Column(String)
	## groups
	memberOf = Column(String) #list, should be extra table
	member = Column(String) #list, should be extra table
	## times
	accountExpires = Column(DateTime)
	badPasswordTime = Column(DateTime)
	lastLogoff = Column(DateTime)
	lastLogon = Column(DateTime)
	lastLogonTimestamp = Column(DateTime)
	pwdLastSet = Column(DateTime)
	whenChanged = Column(DateTime)
	whenCreated = Column(DateTime)
	## security
	badPwdCount = Column(Integer)
	logonCount = Column(Integer)
	sAMAccountType = Column(Integer)
	userAccountControl = Column(Integer)
	
	## other
	codePage = Column(Integer)
	countryCode = Column(Integer)
	
	## calculated properties
	when_pw_change = Column(DateTime)
	when_pw_expires = Column(DateTime)
	must_change_pw = Column(DateTime)
	canLogon = Column(Boolean)
	isAdmin = Column(Boolean)

	credential = relationship("Credential", back_populates="user")
	
	@staticmethod
	def from_aduser(u):
		user = JackDawADUser()
		user.sn = lf(getattr(u,'sn'))
		user.cn = lf(getattr(u,'cn'))
		user.dn = lf(getattr(u,'distinguishedName'))
		user.initials = lf(getattr(u,'initials'))
		user.givenName = lf(getattr(u,'givenName'))
		user.displayName = lf(getattr(u,'displayName'))
		user.name = lf(getattr(u,'name'))
		user.objectCategory = lf(getattr(u,'objectCategory'))
		user.objectClass = lf(getattr(u,'objectClass'))
		user.objectGUID = lf(getattr(u,'objectGUID'))
		user.objectSid = lf(getattr(u,'objectSid'))
		user.primaryGroupID = lf(getattr(u,'primaryGroupID'))
		user.sAMAccountName = lf(getattr(u,'sAMAccountName'))
		user.userPrincipalName = lf(getattr(u,'userPrincipalName'))
		user.servicePrincipalName = lf(getattr(u,'servicePrincipalName'))
	
		user.memberOf = lf(getattr(u,'memberOf'))
		user.member = lf(getattr(u,'member'))
		user.accountExpires = dt(lf(getattr(u,'accountExpires')))
		user.badPasswordTime = dt(lf(getattr(u,'badPasswordTime')))
		user.lastLogoff = dt(lf(getattr(u,'lastLogoff')))
		user.lastLogon = dt(lf(getattr(u,'lastLogon')))
		user.lastLogonTimestamp = dt(lf(getattr(u,'lastLogonTimestamp')))
		user.pwdLastSet = dt(lf(getattr(u,'pwdLastSet')))
		user.whenChanged = dt(lf(getattr(u,'whenChanged')))
		user.whenCreated = dt(lf(getattr(u,'whenCreated')))
		user.badPwdCount = lf(getattr(u,'badPwdCount'))
		user.logonCount = lf(getattr(u,'logonCount'))
		user.sAMAccountType = lf(getattr(u,'sAMAccountType'))
		user.userAccountControl = lf(getattr(u,'userAccountControl'))
	
		user.codePage = lf(getattr(u,'codePage'))
		user.countryCode = lf(getattr(u,'countryCode'))
		user.when_pw_change = dt(lf(getattr(u,'when_pw_change')))
		user.when_pw_expires = dt(lf(getattr(u,'when_pw_expires')))
		user.must_change_pw = dt(lf(getattr(u,'must_change_pw')))
		user.canLogon = bc(lf(getattr(u,'canLogon')))
		user.isAdmin = bc(lf(getattr(u,'isAdmin', None)))
		return user
	
	@staticmethod
	def from_dict(d):
		user = JackDawADUser()
		user.sn = lf(d.get('sn'))
		user.cn = lf(d.get('cn'))
		user.dn = lf(d.get('distinguishedName'))
		user.initials = lf(d.get('initials'))
		user.givenName = lf(d.get('givenName'))
		user.displayName = lf(d.get('displayName'))
		user.name = lf(d.get('name'))
		user.objectCategory = lf(d.get('objectCategory'))
		user.objectClass = lf(d.get('objectClass'))
		user.objectGUID = lf(d.get('objectGUID'))
		user.objectSid = lf(d.get('objectSid'))
		user.primaryGroupID = lf(d.get('primaryGroupID'))
		user.sAMAccountName = lf(d.get('sAMAccountName'))
		user.userPrincipalName = lf(d.get('userPrincipalName'))
		user.servicePrincipalName = lf(d.get('servicePrincipalName'))
	
		user.memberOf = lf(d.get('memberOf'))
		user.member = lf(d.get('member'))
		user.accountExpires = lf(d.get('accountExpires'))
		user.badPasswordTime = lf(d.get('badPasswordTime'))
		user.lastLogoff = lf(d.get('lastLogoff'))
		user.lastLogon = lf(d.get('lastLogon'))
		user.lastLogonTimestamp = lf(d.get('lastLogonTimestamp'))
		user.pwdLastSet = lf(d.get('pwdLastSet'))
		user.whenChanged = lf(d.get('whenChanged'))
		user.whenCreated = lf(d.get('whenCreated'))
		user.badPwdCount = lf(d.get('badPwdCount'))
		user.logonCount = lf(d.get('logonCount'))
		user.sAMAccountType = lf(d.get('sAMAccountType'))
		user.userAccountControl = lf(d.get('userAccountControl'))
	
		user.codePage = lf(d.get('codePage'))
		user.countryCode = lf(d.get('countryCode'))
		user.when_pw_change = lf(d.get('when_pw_change'))
		user.when_pw_expires = lf(d.get('when_pw_expires'))
		user.must_change_pw = lf(d.get('must_change_pw'))
		user.canLogon = lf(d.get('canLogon'))
		user.canLogon = lf(d.get('isAdmin'))
		return user