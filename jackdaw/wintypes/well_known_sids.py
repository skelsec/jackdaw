
#https://support.microsoft.com/en-us/help/243330/well-known-security-identifiers-in-windows-operating-systems

#all of the domain sids start with 'S-1-5-21domain-'
WELL_KNOWN_DOMAIN_SIDS = {
	'500' : 'Administrator', #A user account for the system administrator. By default, it is the only user account that is given full control over the system.
	'501' : 'Guest', #A user account for people who do not have individual accounts. This user account does not require a password. By default, the Guest account is disabled.
	'502' : 'KRBTGT', #A service account that is used by the Key Distribution Center (KDC) service.
	'512' : 'Domain Admins', #A global group whose members are authorized to administer the domain. 
	'513' : 'Domain Users', #A global group whose members are authorized to administer the domain. 
	'514' : 'Domain Guests',
	'515' : 'Domain Computers',
	'516' : 'Domain Controllers',
	'517' : 'Cert Publishers',
	'518' : 'Schema Admins',
	'519' : 'Enterprise Admins',
	'520' : 'Group Policy Creator Owners',
	'526' : 'Key Admins',
	'527' : 'Enterprise Key Admins',
	'553' : 'RAS and IAS Servers',
	'498' : 'Enterprise Read-only Domain Controllers',
	'521' : 'Read-only Domain Controllers',
	'571' : 'Allowed RODC Password Replication Group',
	'572' : 'Denied RODC Password Replication Group',
	'522' : 'Cloneable Domain Controllers',
}

WELL_KNOWN_DOMAIN_SIDS_INV = {v: k for k, v in WELL_KNOWN_DOMAIN_SIDS.items()}

#one extra: 'S-1-5-5-X-Y' : 'Logon Session', #A logon session. The X and Y values for these SIDs are different for each session.
WELL_KNOWN_SIDS = {
	'S-1-0' : 'Null Authority',
	'S-1-0-0' : 'Nobody',
	'S-1-1' : 'World Authority',
	'S-1-1-0' : 'Everyone',
	'S-1-2' : 'Local Authority',
	'S-1-2-0' : 'Local',
	'S-1-2-1' : 'Console Logon',
	'S-1-3' : 'Creator Authority',
	'S-1-3-0' : 'Creator Owner',
	'S-1-3-1' : 'Creator Group',
	'S-1-3-2' : 'Creator Owner Server',
	'S-1-3-3' : 'Creator Group Server',
	'S-1-3-4' : 'Owner Rights',
	'S-1-5-80-0' : 'All Services',
	'S-1-4' : 'Non-unique Authority',
	'S-1-5' : 'NT Authority',
	'S-1-5-1' : 'Dialup',
	'S-1-5-2' : 'Network',
	'S-1-5-3' : 'Batch',
	'S-1-5-4' : 'Interactive',
	'S-1-5-6' : 'Service',
	'S-1-5-7' : 'Anonymous',
	'S-1-5-8' : 'Proxy',
	'S-1-5-9' : 'Enterprise Domain Controllers',
	'S-1-5-10' : 'Principal Self',
	'S-1-5-11' : 'Authenticated Users',
	'S-1-5-12' : 'Restricted Code',
	'S-1-5-13' : 'Terminal Server Users',
	'S-1-5-14' : 'Remote Interactive Logon',
	'S-1-5-15' : 'This Organization',
	'S-1-5-17' : 'This Organization',
	'S-1-5-18' : 'Local System',
	'S-1-5-19' : 'NT Authority',
	'S-1-5-20' : 'NT Authority',
	'S-1-5-32-544' : 'Administrators',
	'S-1-5-32-545' : 'Users',
	'S-1-5-32-546' : 'Guests',
	'S-1-5-32-547' : 'Power Users',
	'S-1-5-32-548' : 'Account Operators',
	'S-1-5-32-549' : 'Server Operators',
	'S-1-5-32-550' : 'Print Operators',
	'S-1-5-32-551' : 'Backup Operators',
	'S-1-5-32-552' : 'Replicators',
	'S-1-5-64-10' : 'NTLM Authentication',
	'S-1-5-64-14' : 'SChannel Authentication',
	'S-1-5-64-21' : 'Digest Authentication',
	'S-1-5-80' : 'NT Service',
	'S-1-5-80-0' : 'NT SERVICES\\ALL SERVICES',
	'S-1-5-83-0' : 'NT VIRTUAL MACHINE\\Virtual Machines',
	'S-1-16-0' : 'Untrusted Mandatory Level',
	'S-1-16-4096' : 'Low Mandatory Level',
	'S-1-16-8192' : 'Medium Mandatory Level',
	'S-1-16-8448' : 'Medium Plus Mandatory Level',
	'S-1-16-12288' : 'High Mandatory Level',
	'S-1-16-16384' : 'System Mandatory Level',
	'S-1-16-20480' : 'Protected Process Mandatory Level',
	'S-1-16-28672' : 'Secure Process Mandatory Level',
	'S-1-5-32-554' : 'BUILTIN\\Pre-Windows 2000 Compatible Access',
	'S-1-5-32-555' : 'BUILTIN\\Remote Desktop Users',
	'S-1-5-32-556' : 'BUILTIN\\Network Configuration Operators',
	'S-1-5-32-557' : 'BUILTIN\\Incoming Forest Trust Builders',
	'S-1-5-32-558' : 'BUILTIN\\Performance Monitor Users',
	'S-1-5-32-559' : 'BUILTIN\\Performance Log Users',
	'S-1-5-32-560' : 'BUILTIN\\Windows Authorization Access Group',
	'S-1-5-32-561' : 'BUILTIN\\Terminal Server License Servers',
	'S-1-5-32-562' : 'BUILTIN\\Distributed COM Users',
	'S-1-5-32-569' : 'BUILTIN\\Cryptographic Operators',
	'S-1-5-32-573' : 'BUILTIN\\Event Log Readers',
	'S-1-5-32-574' : 'BUILTIN\\Certificate Service DCOM Access',
	'S-1-5-32-575' : 'BUILTIN\\RDS Remote Access Servers',
	'S-1-5-32-576' : 'BUILTIN\\RDS Endpoint Servers',
	'S-1-5-32-577' : 'BUILTIN\\RDS Management Servers',
	'S-1-5-32-578' : 'BUILTIN\\Hyper-V Administrators',
	'S-1-5-32-579' : 'BUILTIN\\Access Control Assistance Operators',
	'S-1-5-32-580' : 'BUILTIN\\Remote Management Users',
}

WELL_KNOWN_SIDS_INV = {v: k for k, v in WELL_KNOWN_DOMAIN_SIDS.items()}

def get_sid_for_name(name, domain_sid = None):
	if domain_sid:
		if name in WELL_KNOWN_DOMAIN_SIDS_INV:
			return domain_sid + '-' + WELL_KNOWN_DOMAIN_SIDS_INV[name]
	else:
		if name in WELL_KNOWN_SIDS_INV:
			return WELL_KNOWN_SIDS_INV[name]
			
	return None
	

def get_name_or_sid(sid_str):
	if sid_str[:len('S-1-5-5-')] == 'S-1-5-5-':
		return 'Logon Session'
	if sid_str in WELL_KNOWN_SIDS:
		return WELL_KNOWN_SIDS[sid_str]
	if sid_str[:len('S-1-5-21')] == 'S-1-5-21':
		if sid_str[-3:] in WELL_KNOWN_DOMAIN_SIDS:
			return WELL_KNOWN_DOMAIN_SIDS[sid_str[-3:]]
	return sid_str
			
		