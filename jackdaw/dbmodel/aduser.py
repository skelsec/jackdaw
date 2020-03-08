from . import Basemodel, lf, dt, bc
from jackdaw.dbmodel.utils import *
import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
import json
from jackdaw.utils.encoder import UniversalEncoder

class JackDawADUser(Basemodel):
	__tablename__ = 'users'

	# Now for the attributes
	id = Column(Integer, primary_key=True)
	ad_id = Column(Integer, ForeignKey('ads.id'))
	ad = relationship("JackDawADInfo", back_populates="users", lazy = True)
	fetched_at = Column(DateTime, default=datetime.datetime.utcnow)
	sn = Column(String)
	cn = Column(String)
	dn = Column(String)
	description = Column(String)
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
	
	UAC_SCRIPT = Column(Boolean)
	UAC_ACCOUNTDISABLE = Column(Boolean)
	UAC_HOMEDIR_REQUIRED = Column(Boolean)
	UAC_LOCKOUT = Column(Boolean)
	UAC_PASSWD_NOTREQD = Column(Boolean)
	UAC_PASSWD_CANT_CHANGE = Column(Boolean)
	UAC_ENCRYPTED_TEXT_PASSWORD_ALLOWED = Column(Boolean)
	UAC_TEMP_DUPLICATE_ACCOUNT = Column(Boolean)
	UAC_NORMAL_ACCOUNT = Column(Boolean)
	UAC_INTERDOMAIN_TRUST_ACCOUNT = Column(Boolean)
	UAC_WORKSTATION_TRUST_ACCOUNT = Column(Boolean)
	UAC_SERVER_TRUST_ACCOUNT = Column(Boolean)
	UAC_NA_1 = Column(Boolean)
	UAC_NA_2 = Column(Boolean)
	UAC_DONT_EXPIRE_PASSWD = Column(Boolean)
	UAC_MNS_LOGON_ACCOUNT = Column(Boolean)
	UAC_SMARTCARD_REQUIRED = Column(Boolean)
	UAC_TRUSTED_FOR_DELEGATION = Column(Boolean)
	UAC_NOT_DELEGATED = Column(Boolean)
	UAC_USE_DES_KEY_ONLY = Column(Boolean)
	UAC_DONT_REQUIRE_PREAUTH = Column(Boolean)
	UAC_PASSWORD_EXPIRED = Column(Boolean)
	UAC_TRUSTED_TO_AUTHENTICATE_FOR_DELEGATION = Column(Boolean)

	#credential = relationship("Credential", back_populates="user", lazy = True)
	allowedtodelegateto = relationship("JackDawUserConstrainedDelegation", back_populates="user", lazy = True)
	

	def to_dict(self):
		return {
			'id' : self.id ,
			'ad_id' : self.ad_id ,
			'dn' : self.dn ,
			'givenName' : self.givenName ,
			'displayName' : self.displayName ,
			'description' : self.description,
			'name' : self.name ,
			'objectSid' : self.objectSid ,
			'sAMAccountName' : self.sAMAccountName ,
			'userPrincipalName' : self.userPrincipalName ,
			'servicePrincipalName' : self.servicePrincipalName ,
			'accountExpires' : self.accountExpires ,
			'badPasswordTime' : self.badPasswordTime ,
			'lastLogoff' : self.lastLogoff ,
			'lastLogon' : self.lastLogon ,
			'lastLogonTimestamp' : self.lastLogonTimestamp ,
			'pwdLastSet' : self.pwdLastSet ,
			'whenChanged' : self.whenChanged ,
			'whenCreated' : self.whenCreated ,
			'badPwdCount' : self.badPwdCount ,
			'logonCount' : self.logonCount ,
			'sAMAccountType' : self.sAMAccountType ,
			'userAccountControl' : self.userAccountControl ,
			'codePage' : self.codePage ,
			'countryCode' : self.countryCode ,
			'when_pw_change' : self.when_pw_change ,
			'when_pw_expires' : self.when_pw_expires ,
			'must_change_pw' : self.must_change_pw ,
			'canLogon' : self.canLogon ,
			'UAC_SCRIPT' : self.UAC_SCRIPT ,
			'UAC_ACCOUNTDISABLE' : self.UAC_ACCOUNTDISABLE ,
			'UAC_HOMEDIR_REQUIRED' : self.UAC_HOMEDIR_REQUIRED ,
			'UAC_LOCKOUT' : self.UAC_LOCKOUT ,
			'UAC_PASSWD_NOTREQD' : self.UAC_PASSWD_NOTREQD ,
			'UAC_PASSWD_CANT_CHANGE' : self.UAC_PASSWD_CANT_CHANGE ,
			'UAC_ENCRYPTED_TEXT_PASSWORD_ALLOWED' : self.UAC_ENCRYPTED_TEXT_PASSWORD_ALLOWED ,
			'UAC_TEMP_DUPLICATE_ACCOUNT' : self.UAC_TEMP_DUPLICATE_ACCOUNT ,
			'UAC_NORMAL_ACCOUNT' : self.UAC_NORMAL_ACCOUNT ,
			'UAC_INTERDOMAIN_TRUST_ACCOUNT' : self.UAC_INTERDOMAIN_TRUST_ACCOUNT ,
			'UAC_WORKSTATION_TRUST_ACCOUNT' : self.UAC_WORKSTATION_TRUST_ACCOUNT ,
			'UAC_SERVER_TRUST_ACCOUNT' : self.UAC_SERVER_TRUST_ACCOUNT ,
			'UAC_DONT_EXPIRE_PASSWD' : self.UAC_DONT_EXPIRE_PASSWD ,
			'UAC_MNS_LOGON_ACCOUNT' : self.UAC_MNS_LOGON_ACCOUNT ,
			'UAC_SMARTCARD_REQUIRED' : self.UAC_SMARTCARD_REQUIRED ,
			'UAC_TRUSTED_FOR_DELEGATION' : self.UAC_TRUSTED_FOR_DELEGATION ,
			'UAC_NOT_DELEGATED' : self.UAC_NOT_DELEGATED ,
			'UAC_USE_DES_KEY_ONLY' : self.UAC_USE_DES_KEY_ONLY ,
			'UAC_DONT_REQUIRE_PREAUTH' : self.UAC_DONT_REQUIRE_PREAUTH ,
			'UAC_PASSWORD_EXPIRED' : self.UAC_PASSWORD_EXPIRED ,
			'UAC_TRUSTED_TO_AUTHENTICATE_FOR_DELEGATION' : self.UAC_TRUSTED_TO_AUTHENTICATE_FOR_DELEGATION ,
		}

	def to_json(self):
		return json.dumps(self.to_dict(), cls=UniversalEncoder)

	@staticmethod
	def from_aduser(u):
		user = JackDawADUser()
		user.sn = lf(getattr(u,'sn'))
		user.cn = lf(getattr(u,'cn'))
		user.dn = lf(getattr(u,'distinguishedName'))
		user.description = lf(getattr(u,'description'))
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
		calc_uac_flags(user)
			
		return user