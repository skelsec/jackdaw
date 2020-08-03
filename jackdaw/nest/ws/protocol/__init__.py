

import json
import enum

from jackdaw.utils.encoder import UniversalEncoder
from jackdaw.nest.ws.protocol.cmdtypes import *
from jackdaw.nest.ws.protocol.changead import NestOpChangeAD
from jackdaw.nest.ws.protocol.changegraph import NestOpChangeGraph
from jackdaw.nest.ws.protocol.error import NestOpErr
from jackdaw.nest.ws.protocol.gather import NestOpGather
from jackdaw.nest.ws.protocol.getobjinfo import NestOpGetOBJInfo
from jackdaw.nest.ws.protocol.kerberoast import NestOpKerberoast
from jackdaw.nest.ws.protocol.listad import NestOpListAD, NestOpListADRes
from jackdaw.nest.ws.protocol.listgraph import NestOpListGraphs
from jackdaw.nest.ws.protocol.log import NestOpLog
from jackdaw.nest.ws.protocol.ok import NestOpOK
from jackdaw.nest.ws.protocol.pathda import NestOpPathDA
from jackdaw.nest.ws.protocol.pathshortest import NestOpPathShortest
from jackdaw.nest.ws.protocol.smbsessions import NestOpSMBSessions
from jackdaw.nest.ws.protocol.tcpscan import NestOpTCPScan, NestOpTCPScanRes
from jackdaw.nest.ws.protocol.pathres import NestOpPathRes
from jackdaw.nest.ws.protocol.gatherstatus import NestOpGatherStatus
from jackdaw.nest.ws.protocol.user import NestOpUserRes

__all__ = [
	'NestOpCmd',
	'NestOpCmdDeserializer',
	'NestOpTCPScanRes',
	'NestOpTCPScan',
	'NestOpSMBSessions',
	'NestOpPathShortest',
	'NestOpPathDA',
	'NestOpOK',
	'NestOpLog',
	'NestOpListGraphs',
	'NestOpListAD',
	'NestOpKerberoast',
	'NestOpGetOBJInfo',
	'NestOpGather',
	'NestOpErr',
	'NestOpChangeGraph',
	'NestOpChangeAD',
	'NestOpListADRes',
	'NestOpPathRes',
	'NestOpGatherStatus',
	'NestOpUserRes',
]


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
	NestOpCmd.LISTGRAPHS : NestOpListGraphs,
	NestOpCmd.CHANGEGRAPH : NestOpChangeGraph,
	NestOpCmd.TCPSCAN: NestOpTCPScan,
	NestOpCmd.TCPSCANRES: NestOpTCPScanRes,
	NestOpCmd.LISTADSRES: NestOpListADRes,
	NestOpCmd.PATHRES: NestOpPathRes,
	NestOpCmd.GATHERSTATUS: NestOpGatherStatus,
	NestOpCmd.USERRES: NestOpUserRes,
	
}