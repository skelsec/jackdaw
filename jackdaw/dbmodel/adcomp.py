import datetime
import hashlib

from . import Basemodel, lf, dt, bc

from sqlalchemy.orm import relationship
from sqlalchemy import Index, func
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from jackdaw.dbmodel.utils.serializer import Serializer
from jackdaw.dbmodel.utils.uacflags import calc_uac_flags

class Machine(Basemodel, Serializer):
	__tablename__ = 'admachines'

	# Now for the attributes
	id = Column(Integer, primary_key=True)
	ad_id = Column(Integer, ForeignKey('adinfo.id'))
	sn = Column(String)
	cn = Column(String)
	dn = Column(String)
	accountExpires = Column(DateTime)
	badPasswordTime = Column(DateTime)
	badPwdCount = Column(String)
	codePage = Column(String)
	countryCode = Column(String)
	description = Column(String)
	displayName = Column(String)
	dNSHostName = Column(String, index=True)
	instanceType = Column(String)
	isCriticalSystemObject = Column(String)
	lastLogoff =Column(DateTime)
	lastLogon = Column(DateTime)
	lastLogonTimestamp = Column(DateTime)
	logonCount = Column(Integer)
	localPolicyFlags = Column(String)
	supported_enc_types = Column(Integer)
	name = Column(String)
	nTSecurityDescriptor = Column(String)
	objectCategory = Column(String)
	objectClass = Column(String)
	objectGUID = Column(String, index=True)
	objectSid = Column(String)
	operatingSystem = Column(String)
	operatingSystemVersion = Column(String)
	primaryGroupID = Column(String)
	pwdLastSet = Column(DateTime)
	sAMAccountName = Column(String)
	sAMAccountType = Column(String)
	userAccountControl = Column(Integer)
	whenChanged = Column(DateTime)
	whenCreated = Column(DateTime)
	servicePrincipalName = Column(String)
	
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
	Index('machinednslower', func.lower(dNSHostName))

	def gen_checksum(self):
		ctx = hashlib.md5()
		ctx.update(str(self.sAMAccountName).encode())
		ctx.update(str(self.userAccountControl).encode())
		#ctx.update(str(self.adminCount))
		ctx.update(str(self.sAMAccountType).encode())
		ctx.update(str(self.dn).encode())
		ctx.update(str(self.cn).encode())
		ctx.update(str(self.servicePrincipalName).encode())
		self.checksum = ctx.hexdigest()

	def to_dict(self):
		return {
			'id' : self.id ,
			'ad_id' : self.ad_id ,
			'dn' : self.dn ,
			'displayName' : self.displayName ,
			'description' : self.description,
			'name' : self.name ,
			'objectSid' : self.objectSid ,
			'sAMAccountName' : self.sAMAccountName ,
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
			'supported_enc_types' : self.supported_enc_types ,
			'localPolicyFlags' : self.localPolicyFlags ,
			'operatingSystem' : self.operatingSystem ,
			'operatingSystemVersion' : self.operatingSystemVersion ,
			'primaryGroupID' : self.primaryGroupID ,
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
			'when_pw_change' : self.when_pw_change ,
			'when_pw_expires' : self.when_pw_expires ,
			'must_change_pw' : self.must_change_pw ,
			'canLogon' : self.canLogon ,
			'checksum' : self.checksum,
		}
	
	@staticmethod
	def from_adcomp(u):
		machine = Machine()
		machine.sn = u.sn
		machine.cn = u.cn
		machine.dn = u.distinguishedName
		machine.description = u.description
		machine.accountExpires = dt(u.accountExpires)
		machine.badPasswordTime = dt(u.badPasswordTime)
		machine.badPwdCount = u.badPwdCount
		machine.codePage = u.codePage
		machine.countryCode = u.countryCode
		machine.displayName = u.displayName
		machine.dNSHostName = u.dNSHostName
		machine.instanceType = u.instanceType
		machine.isCriticalSystemObject = u.isCriticalSystemObject
		machine.lastLogoff = dt(u.lastLogoff)
		machine.lastLogon = dt(u.lastLogon)
		machine.lastLogonTimestamp = dt(u.lastLogonTimestamp)
		machine.logonCount = u.logonCount
		machine.localPolicyFlags = u.localPolicyFlags
		machine.supported_enc_types = u.supported_enc_types
		machine.name = u.name
		machine.nTSecurityDescriptor = u.nTSecurityDescriptor
		machine.objectCategory = u.objectCategory
		machine.objectClass = lf(u.objectClass)
		machine.objectGUID = u.objectGUID
		machine.objectSid = u.objectSid
		machine.operatingSystem = u.operatingSystem
		machine.operatingSystemVersion = u.operatingSystemVersion
		machine.primaryGroupID = u.primaryGroupID
		machine.pwdLastSet = dt(u.pwdLastSet)
		machine.sAMAccountName = u.sAMAccountName
		machine.sAMAccountType = u.sAMAccountType
		machine.userAccountControl = lf(int(getattr(u,'userAccountControl', 0)))
		machine.whenChanged = dt(u.whenChanged)
		machine.whenCreated = dt(u.whenCreated)
		machine.servicePrincipalName = lf(u.servicePrincipalName)
		
		machine.when_pw_change = dt(u.when_pw_change)
		machine.when_pw_expires = dt(u.when_pw_expires)
		machine.must_change_pw = dt(u.must_change_pw)
		machine.canLogon = bc(u.canLogon)
		
		calc_uac_flags(machine)
		machine.gen_checksum()
		
		return machine