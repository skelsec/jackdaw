import enum


class LDAPAgentCommand(enum.Enum):
	SPNSERVICE = 0
	SPNSERVICES = 1
	USER = 2
	USERS = 3
	MACHINE = 4
	MACHINES = 5
	OU = 6
	OUS = 7
	DOMAININFO = 8
	GROUP = 9
	GROUPS = 10
	MEMBERSHIP = 11
	MEMBERSHIPS = 12
	SD = 13
	SDS = 14
	GPO = 15
	GPOS = 16
	TRUSTS = 17
	SCHEMA = 18
	EXCEPTION = 99

	SPNSERVICES_FINISHED = 31
	USERS_FINISHED = 32
	MACHINES_FINISHED = 33
	OUS_FINISHED = 34
	GROUPS_FINISHED = 35
	MEMBERSHIPS_FINISHED = 36
	SDS_FINISHED = 37
	DOMAININFO_FINISHED = 38
	GPOS_FINISHED = 39
	TRUSTS_FINISHED = 40
	MEMBERSHIP_FINISHED = 41
	SCHEMA_FINISHED = 42

MSLDAP_JOB_TYPES = {
	'users' : LDAPAgentCommand.USERS_FINISHED ,
	'machines' : LDAPAgentCommand.MACHINES_FINISHED ,
	'sds' : LDAPAgentCommand.SDS_FINISHED ,
	'memberships' : LDAPAgentCommand.MEMBERSHIPS_FINISHED ,
	'ous' : LDAPAgentCommand.OUS_FINISHED ,
	'gpos' : LDAPAgentCommand.GPOS_FINISHED ,
	'groups' : LDAPAgentCommand.GROUPS_FINISHED ,
	'spns' : LDAPAgentCommand.SPNSERVICES_FINISHED ,
	'adinfo' : LDAPAgentCommand.DOMAININFO_FINISHED,
	'trusts' : LDAPAgentCommand.TRUSTS_FINISHED,
	'schema' : LDAPAgentCommand.SCHEMA_FINISHED,
}
MSLDAP_JOB_TYPES_INV = {v: k for k, v in MSLDAP_JOB_TYPES.items()}

class LDAPAgentJob:
	def __init__(self, command, data):
		self.command = command
		self.data = data