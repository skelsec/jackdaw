from . import Basemodel, lf, dt
from jackdaw.dbmodel.utils import *
import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean

class JackDawADMachine(Basemodel):
	__tablename__ = 'machines'

	# Now for the attributes
	id = Column(Integer, primary_key=True)
	ad_id = Column(Integer, ForeignKey('ads.id'))
	ad = relationship("JackDawADInfo", back_populates="computers", lazy = True)
	fetched_at = Column(DateTime, default=datetime.datetime.utcnow)
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
	dNSHostName = Column(String)
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
	objectGUID = Column(String)
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
	
	allowedtodelegateto = relationship("JackDawMachineConstrainedDelegation", back_populates="machine", lazy = True)
	
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
		}
	
	@staticmethod
	def from_adcomp(u):
		machine = JackDawADMachine()
		machine.sn = lf(getattr(u,'sn'))
		machine.cn = lf(getattr(u,'cn'))
		machine.dn = lf(getattr(u,'distinguishedName'))
		machine.description = lf(getattr(u,'description'))
		machine.accountExpires = dt(lf(getattr(u,'accountExpires')))
		machine.badPasswordTime = dt(lf(getattr(u,'badPasswordTime')))
		machine.badPwdCount = lf(getattr(u,'badPwdCount'))
		machine.codePage = lf(getattr(u,'codePage'))
		machine.countryCode = lf(getattr(u,'countryCode'))
		machine.displayName = lf(getattr(u,'displayName'))
		machine.dNSHostName = lf(getattr(u,'dNSHostName'))
		machine.instanceType = lf(getattr(u,'instanceType'))
		machine.isCriticalSystemObject = lf(getattr(u,'isCriticalSystemObject'))
		machine.lastLogoff = dt(lf(getattr(u,'lastLogoff')))
		machine.lastLogon = dt(lf(getattr(u,'lastLogon')))
		machine.lastLogonTimestamp = dt(lf(getattr(u,'lastLogonTimestamp')))
		machine.logonCount = lf(getattr(u,'logonCount'))
		machine.localPolicyFlags = lf(getattr(u,'localPolicyFlags'))
		machine.supported_enc_types = lf(getattr(u,'supported_enc_types'))
		machine.name = lf(getattr(u,'name'))
		machine.nTSecurityDescriptor = lf(getattr(u,'nTSecurityDescriptor'))
		machine.objectCategory = lf(getattr(u,'objectCategory'))
		machine.objectClass = lf(getattr(u,'objectClass'))
		machine.objectGUID = lf(getattr(u,'objectGUID'))
		machine.objectSid = lf(getattr(u,'objectSid'))
		machine.operatingSystem = lf(getattr(u,'operatingSystem'))
		machine.operatingSystemVersion = lf(getattr(u,'operatingSystemVersion'))
		machine.primaryGroupID = lf(getattr(u,'primaryGroupID'))
		machine.pwdLastSet = dt(lf(getattr(u,'pwdLastSet')))
		machine.sAMAccountName = lf(getattr(u,'sAMAccountName'))
		machine.sAMAccountType = lf(getattr(u,'sAMAccountType'))
		machine.userAccountControl = lf(int(getattr(u,'userAccountControl', 0)))
		machine.whenChanged = dt(lf(getattr(u,'whenChanged')))
		machine.whenCreated = dt(lf(getattr(u,'whenCreated')))
		machine.servicePrincipalName = lf(getattr(u,'servicePrincipalName'))
		calc_uac_flags(machine)
		
		return machine