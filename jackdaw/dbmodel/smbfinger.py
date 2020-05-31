from . import Basemodel
import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from jackdaw.dbmodel.utils.serializer import Serializer

class SMBFinger(Basemodel, Serializer):
	__tablename__ = 'smbfinger'
	
	id = Column(Integer, primary_key=True)
	ad_id = Column(Integer, index=True)
	machine_sid = Column(String, index=True)
	signing_enabled = Column(Boolean, index=True)
	signing_required = Column(Boolean, index=True)
	domainname = Column(String, index=True)
	computername = Column(String, index=True)
	dnscomputername = Column(String, index=True)
	dnsdomainname = Column(String, index=True)
	local_time = Column(DateTime, index=True)
	dnsforestname = Column(String, index=True)
	os_major_version = Column(String, index=True)
	os_minor_version = Column(String, index=True)
	os_build = Column(String, index=True)
	os_guess = Column(String, index=True)
	
	@staticmethod
	def from_extra_info(machine_sid, extra_info):
		f = SMBFinger()
		f.machine_sid = machine_sid
		if 'signing_enabled' in extra_info:
			f.signing_enabled = extra_info['signing_enabled']
		if 'signing_required' in extra_info:
			f.signing_required = extra_info['signing_required']
		if 'ntlm_data' in extra_info:
			f.domainname = extra_info['ntlm_data']['domainname']
			f.computername = extra_info['ntlm_data']['computername']
			f.dnscomputername = extra_info['ntlm_data']['dnscomputername']
			f.dnsdomainname = extra_info['ntlm_data']['dnsdomainname']
			f.local_time = extra_info['ntlm_data']['local_time']
			f.dnsforestname = extra_info['ntlm_data']['dnsforestname']
			f.os_major_version = extra_info['ntlm_data']['os_major_version']
			f.os_minor_version = extra_info['ntlm_data']['os_minor_version']
			f.os_build = extra_info['ntlm_data']['os_build']
			f.os_guess = extra_info['ntlm_data']['os_guess']

		return f