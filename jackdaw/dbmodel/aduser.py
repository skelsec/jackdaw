from . import Basemodel, lf, dt, bc
from jackdaw.dbmodel.utils.uacflags import calc_uac_flags
import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
import json
from jackdaw.utils.encoder import UniversalEncoder
from jackdaw.dbmodel.utils.serializer import Serializer
import hashlib

class ADUser(Basemodel, Serializer):
	__tablename__ = 'users'

	# Now for the attributes
	id = Column(Integer, primary_key=True)
	ad_id = Column(Integer, ForeignKey('adinfo.id'))
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
	objectGUID = Column(String, index=True)
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
	adminCount = Column(Integer)
	
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

	checksum = Column(String, index = True)

	def gen_checksum(self):
		ctx = hashlib.md5()
		ctx.update(str(self.sAMAccountName).encode())
		ctx.update(str(self.userAccountControl).encode())
		ctx.update(str(self.adminCount).encode())
		ctx.update(str(self.sAMAccountType).encode())
		ctx.update(str(self.dn).encode())
		ctx.update(str(self.cn).encode())
		ctx.update(str(self.servicePrincipalName).encode())
		ctx.update(str(self.memberOf).encode())
		ctx.update(str(self.member).encode())
		self.checksum = ctx.hexdigest()

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
			'adminCount' : self.adminCount,
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
			'checksum' : self.checksum,
		}

	def to_json(self):
		return json.dumps(self.to_dict(), cls=UniversalEncoder)

	@staticmethod
	def from_aduser(u):
		user = ADUser()
		user.sn = u.sn
		user.cn = u.cn
		user.dn = u.distinguishedName
		user.description = u.description
		user.initials = u.initials
		user.givenName = u.givenName
		user.displayName = u.displayName
		user.name = u.name
		user.objectCategory = u.objectCategory
		user.objectClass = lf(u.objectClass)
		user.objectGUID = u.objectGUID
		user.objectSid = u.objectSid
		user.primaryGroupID = u.primaryGroupID
		user.sAMAccountName = u.sAMAccountName
		user.userPrincipalName = lf(u.userPrincipalName)
		user.servicePrincipalName = lf(u.servicePrincipalName)
	
		user.memberOf = lf(u.memberOf)
		user.member = lf(u.member)
		user.accountExpires = dt(u.accountExpires)
		user.badPasswordTime = dt(u.badPasswordTime)
		user.lastLogoff = dt(u.lastLogoff)
		user.lastLogon = dt(u.lastLogon)
		user.lastLogonTimestamp = dt(u.lastLogonTimestamp)
		user.pwdLastSet = dt(u.pwdLastSet)
		user.whenChanged = dt(u.whenChanged)
		user.whenCreated = dt(u.whenCreated)
		user.badPwdCount = u.badPwdCount
		user.logonCount = u.logonCount
		user.sAMAccountType = u.sAMAccountType
		try:
			user.userAccountControl = int(u.userAccountControl)
		except:
			pass
		
		user.codePage = u.codePage
		user.countryCode = u.countryCode
		user.when_pw_change = dt(u.when_pw_change)
		user.when_pw_expires = dt(u.when_pw_expires)
		user.must_change_pw = dt(u.must_change_pw)
		user.adminCount = u.admincount
		user.canLogon = bc(u.canLogon)
		user.isAdmin = bc(getattr(u,'isAdmin', None))
		calc_uac_flags(user)
		user.gen_checksum()
		return user