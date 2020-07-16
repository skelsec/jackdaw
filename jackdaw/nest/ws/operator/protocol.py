
import json
import enum

from jackdaw.utils.encoder import UniversalEncoder

class NestOpCmd(enum.Enum):
	GATHER = 'GATHER'
	KERBEROAST = 'KERBEROAST'
	SMBSESSIONS = 'SMBSESSIONS'
	PATHSHORTEST = 'PATHSHORTEST'
	PATHDA = 'PATHDA'
	GETOBJINFO = 'GETOBJINFO'
	CHANGEAD = 'CHANGEAD'
	LISTADS = 'LISTADS'
	OK = 'OK'
	ERR = 'ERR'
	LOG = 'LOG'
	RESULT = 'RESULT'
	LISTGRAPHS = 'LISTGRAPHS'
	CHANGEGRAPH = 'CHANGEGRAPH'
	TCPSCAN = 'TCPSCAN'

class NestOpCmdDeserializer:
	def __init__(self):
		pass

	@staticmethod
	def from_dict(d):
		cmdtype = NestOpCmd(d['cmd'])
		return type2obj[cmdtype].from_dict(d)

	@staticmethod
	def from_json(jd):
		return NestOpCmdDeserializer.from_dict(json.loads(jd))

class NestOpGather:
	def __init__(self):
		self.cmd = NestOpCmd.GATHER
		self.token = None
		self.ldap_url = None
		self.smb_url = None
		self.kerberos_url = None
		self.ldap_workers = 4
		self.smb_worker_cnt = 500
		self.dns = None
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpGather()
		cmd.token = d['token']
		cmd.ldap_url = d['ldap_url']
		cmd.smb_url = d['smb_url']
		cmd.kerberos_url = d['kerberos_url']
		if 'ldap_workers' in d:
			cmd.exclude = d['ldap_workers']
		if 'smb_worker_cnt' in d:
			cmd.exclude = d['smb_worker_cnt']
		if 'dns' in d:
			cmd.exclude = d['dns']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpGather.from_dict(json.loads(jd))

class NestOpKerberoast:
	def __init__(self):
		self.cmd = NestOpCmd.KERBEROAST
		self.token = None
		self.kerberos_url = None
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpKerberoast()
		cmd.token = d['token']
		cmd.kerberos_url = d['kerberos_url']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpKerberoast.from_dict(json.loads(jd))

class NestOpSMBSessions:
	def __init__(self):
		self.cmd = NestOpCmd.SMBSESSIONS
		self.token = None
		self.smb_url = None
		self.all_hosts = False
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpSMBSessions()
		cmd.token = d['token']
		cmd.smb_url = d['smb_url']
		if 'all_hosts' in d:
			cmd.all_hosts = d['all_hosts']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpSMBSessions.from_dict(json.loads(jd))


class NestOpPathShortest:
	def __init__(self):
		self.cmd = NestOpCmd.PATHSHORTEST
		self.token = None
		self.to_sid = None
		self.from_sid = False
		self.exclude = []
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpPathShortest()
		cmd.token = d['token']
		if 'to_sid' in d:
			cmd.to_sid = d['to_sid']
		if 'from_sid' in d:
			cmd.from_sid = d['from_sid']
		if 'exclude' in d:
			cmd.exclude = d['exclude']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpPathShortest.from_dict(json.loads(jd))

class NestOpPathDA:
	def __init__(self):
		self.cmd = NestOpCmd.PATHDA
		self.token = None
		self.exclude = []
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpPathDA()
		cmd.token = d['token']
		if 'exclude' in d:
			cmd.exclude = d['exclude']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpPathDA.from_dict(json.loads(jd))

class NestOpGetOBJInfo:
	def __init__(self):
		self.cmd = NestOpCmd.GETOBJINFO
		self.token = None
		self.oid = None
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpGetOBJInfo()
		cmd.oid = d['oid']
		cmd.token = d['token']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpGetOBJInfo.from_dict(json.loads(jd))

class NestOpChangeAD:
	def __init__(self):
		self.cmd = NestOpCmd.CHANGEAD
		self.token = None
		self.adid = None
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpChangeAD()
		cmd.adid = d['adid']
		cmd.token = d['token']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpChangeAD.from_dict(json.loads(jd))

class NestOpListAD:
	def __init__(self):
		self.cmd = NestOpCmd.LISTADS
		self.token = None
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpListAD()
		cmd.token = d['token']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpListAD.from_dict(json.loads(jd))

class NestOpOK:
	def __init__(self):
		self.cmd = NestOpCmd.OK
		self.token = None
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpOK()
		cmd.token = d['token']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpOK.from_dict(json.loads(jd))

class NestOpErr:
	def __init__(self):
		self.cmd = NestOpCmd.ERR
		self.token = None
		self.reason = None
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpErr()
		cmd.token = d['token']
		if 'reason' in d:
			cmd.reason = d['reason']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpErr.from_dict(json.loads(jd))

class NestOpLog:
	def __init__(self):
		self.cmd = NestOpCmd.LOG
		self.level = None
		self.msg = None
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpLog()
		cmd.level = d['level']
		cmd.msg = d['msg']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpLog.from_dict(json.loads(jd))

class NestOpResult:
	def __init__(self):
		self.cmd = NestOpCmd.RESULT
		self.restype = None
		self.token = None
		self.data = None
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpResult()
		cmd.restype = NestOpCmd(d['restype'])
		cmd.token = d['token']
		cmd.data = d['data']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpResult.from_dict(json.loads(jd))

class NestOpListGraphs:
	def __init__(self):
		self.cmd = NestOpCmd.LISTGRAPHS
		self.token = None
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpListGraphs()
		cmd.token = d['token']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpListGraphs.from_dict(json.loads(jd))

class NestOpChangeGraph:
	def __init__(self):
		self.cmd = NestOpCmd.CHANGEGRAPH
		self.token = None
		self.graphid = None
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpChangeGraph()
		cmd.token = d['token']
		cmd.graphid = d['graphid']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpChangeGraph.from_dict(json.loads(jd))

class NestOpTCPScan:
	def __init__(self):
		self.cmd = NestOpCmd.TCPSCAN
		self.token = None
		self.targets = []
		self.ports = []
		self.settings = None
	
	def to_dict(self):
		return self.__dict__
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	@staticmethod
	def from_dict(d):
		cmd = NestOpTCPScan()
		cmd.token = d['token']
		cmd.targets = d['targets']
		cmd.ports = d['ports']
		cmd.settings = d['settings']
		return cmd

	@staticmethod
	def from_json(jd):
		return NestOpTCPScan.from_dict(json.loads(jd))

type2obj = {
	NestOpCmd.GATHER : NestOpGather,
	NestOpCmd.KERBEROAST : NestOpKerberoast,
	NestOpCmd.SMBSESSIONS : NestOpSMBSessions,
	NestOpCmd.PATHSHORTEST : NestOpPathShortest,
	NestOpCmd.PATHDA : NestOpPathDA,
	NestOpCmd.GETOBJINFO : NestOpGetOBJInfo,
	NestOpCmd.CHANGEAD : NestOpChangeAD,
	NestOpCmd.LISTADS : NestOpListAD,
	NestOpCmd.OK : NestOpOK,
	NestOpCmd.ERR : NestOpErr,
	NestOpCmd.LOG : NestOpLog,
	NestOpCmd.RESULT : NestOpResult,
	NestOpCmd.LISTGRAPHS : NestOpListGraphs,
	NestOpCmd.CHANGEGRAPH : NestOpChangeGraph,
	NestOpCmd.TCPSCAN: NestOpTCPScan,
	
}

