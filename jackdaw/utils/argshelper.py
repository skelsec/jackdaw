
from urllib.parse import urlparse

from aiosmb.commons.connection.url import SMBConnectionURL
from msldap.commons.url import MSLDAPURLDecoder

def argchecker(args, param_name, module_name):
	if not hasattr(args, param_name):
		raise Exception('"%s" parameter is mandatory for "%s" operation' % (param_name, module_name))
	if getattr(args, param_name) is None:
		raise Exception('"%s" parameter is mandatory for "%s" operation' % (param_name, module_name))

def construct_smbdef(args):
	return SMBConnectionURL(args.smb_url) #SMBConnectionManager(args.smb_credential_string, proxy_connection_string = args.sproxy)

def construct_ldapdef(args):
	ldap_url = args.ldap_url
	if ldap_url[-1] == '/':
		ldap_url = args.ldap_url[:-1]
	if hasattr(args, 'same_query') and args.same_query is True and args.smb_url is not None:
		ldap_url = '%s/?%s' % (ldap_url, urlparse(args.smb_url).query)
	return MSLDAPURLDecoder(ldap_url)
