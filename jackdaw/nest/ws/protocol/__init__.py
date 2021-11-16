

import json
import enum

from jackdaw.utils.encoder import UniversalEncoder

from jackdaw.nest.ws.protocol.cmdtypes import *
from jackdaw.nest.ws.protocol.log import NestOpLog
from jackdaw.nest.ws.protocol.ok import NestOpOK
from jackdaw.nest.ws.protocol.error import NestOpErr
from jackdaw.nest.ws.protocol.cancel import NestOpCancel

from jackdaw.nest.ws.protocol.gather.gather import NestOpGather
from jackdaw.nest.ws.protocol.gather.getobjinfo import NestOpGetOBJInfo
from jackdaw.nest.ws.protocol.gather.gatherstatus import NestOpGatherStatus

from jackdaw.nest.ws.protocol.kerberos.kerberoast import NestOpKerberoast, NestOpKerberoastRes
from jackdaw.nest.ws.protocol.kerberos.asreproast import NestOpASREPRoast, NestOpASREPRoastRes
from jackdaw.nest.ws.protocol.kerberos.gettgs import NestOpKerberosTGS, NestOpKerberosTGSRes
from jackdaw.nest.ws.protocol.kerberos.gettgt import NestOpKerberosTGT, NestOpKerberosTGTRes

from jackdaw.nest.ws.protocol.graph.listgraph import NestOpListGraph
from jackdaw.nest.ws.protocol.graph.listgraphres import NestOpListGraphRes
from jackdaw.nest.ws.protocol.graph.loadgraph import NestOpLoadGraph
from jackdaw.nest.ws.protocol.graph.changegraph import NestOpChangeGraph
from jackdaw.nest.ws.protocol.graph.pathda import NestOpPathDA
from jackdaw.nest.ws.protocol.graph.pathshortest import NestOpPathShortest
from jackdaw.nest.ws.protocol.graph.edge import NestOpEdgeRes, NestOpEdgeBuffRes
from jackdaw.nest.ws.protocol.graph.pathres import NestOpPathRes
from jackdaw.nest.ws.protocol.graph.pathkerbroast import NestOpPathKerbroast
from jackdaw.nest.ws.protocol.graph.pathasrep import NestOpPathASREPRoast
from jackdaw.nest.ws.protocol.graph.pathowned import NestOpPathOwned
from jackdaw.nest.ws.protocol.graph.objowned import NestOpObjOwned
from jackdaw.nest.ws.protocol.graph.objhvt import NestOpObjHVT


from jackdaw.nest.ws.protocol.domain.changead import NestOpChangeAD
from jackdaw.nest.ws.protocol.domain.listad import NestOpListAD, NestOpListADRes
from jackdaw.nest.ws.protocol.domain.loadad import NestOpLoadAD
from jackdaw.nest.ws.protocol.domain.user import NestOpUserRes, NestOpUserBuffRes
from jackdaw.nest.ws.protocol.domain.computer import NestOpComputerRes, NestOpComputerBuffRes
from jackdaw.nest.ws.protocol.domain.group import NestOpGroupRes, NestOpGroupBuffRes

from jackdaw.nest.ws.protocol.smb.smbsessions import NestOpSMBSessions
from jackdaw.nest.ws.protocol.smb.smbsessionres import NestOpSMBSessionRes
from jackdaw.nest.ws.protocol.smb.smbshareres import NestOpSMBShareRes, NestOpSMBShareBuffRes
from jackdaw.nest.ws.protocol.smb.smblocalgroupres import NestOpSMBLocalGroupRes
from jackdaw.nest.ws.protocol.smb.smbfiles import NestOpSMBFiles
from jackdaw.nest.ws.protocol.smb.smbfileres import NestOpSMBFileRes
from jackdaw.nest.ws.protocol.smb.smbdcsync import NestOpSMBDCSync


from jackdaw.nest.ws.protocol.scan.tcpscan import NestOpTCPScan, NestOpTCPScanRes

from jackdaw.nest.ws.protocol.customcred.credres import NestOpCredRes
from jackdaw.nest.ws.protocol.customcred.listcred import NestOpListCred
from jackdaw.nest.ws.protocol.customcred.addcred import NestOpAddCred
from jackdaw.nest.ws.protocol.customcred.getcred import NestOpGetCred

from jackdaw.nest.ws.protocol.customtarget.gettarget import NestOpGetTarget
from jackdaw.nest.ws.protocol.customtarget.targetres import NestOpTargetRes
from jackdaw.nest.ws.protocol.customtarget.listtarget import NestOpListTarget
from jackdaw.nest.ws.protocol.customtarget.addtarget import NestOpAddTarget

from jackdaw.nest.ws.protocol.agent.agent import NestOpAgent, NestOpListAgents

from jackdaw.nest.ws.protocol.wsnet.proxyconnect import NestOpWSNETRouterconnect
from jackdaw.nest.ws.protocol.wsnet.proxydisconnect import NestOpWSNETRouterdisconnect
from jackdaw.nest.ws.protocol.wsnet.proxy import NestOpWSNETRouter
from jackdaw.nest.ws.protocol.wsnet.proxylist import NestOpWSNETListRouters

from jackdaw.nest.ws.protocol.credsdef import NestOpCredsDef
from jackdaw.nest.ws.protocol.targetdef import NestOpTargetDef

from jackdaw.nest.ws.protocol.rdp.rdpconnect import NestOpRDPConnect
from jackdaw.nest.ws.protocol.rdp.rdprect import NestOpRDPRectangle
from jackdaw.nest.ws.protocol.rdp.rdpmouse import NestOpRDPMouse

__all__ = [
	'NestOpCmd',
	'NestOpCmdDeserializer',
	'NestOpTCPScanRes',
	'NestOpTCPScan',
	'NestOpSMBSessions',
	'NestOpPathShortest',
	'NestOpPathDA',
	'NestOpOK',
	'NestOpCancel',
	'NestOpLog',
	'NestOpListAD',
	'NestOpKerberoast',
	'NestOpKerberoastRes',
	'NestOpASREPRoast',
	'NestOpASREPRoastRes',
	'NestOpKerberosTGS', 
	'NestOpKerberosTGSRes',
	'NestOpKerberosTGT',
	'NestOpKerberosTGTRes',
	'NestOpGetOBJInfo',
	'NestOpGather',
	'NestOpErr',
	'NestOpChangeGraph',
	'NestOpChangeAD',
	'NestOpListADRes',
	'NestOpPathRes',
	'NestOpGatherStatus',
	'NestOpUserRes',
	'NestOpComputerRes',
	'NestOpSMBSessionRes',
	'NestOpSMBShareRes',
	'NestOpSMBLocalGroupRes',
	'NestOpLoadAD',
	'NestOpGroupRes',
	'NestOpEdgeRes',
	'NestOpEdgeBuffRes',
	'NestOpUserBuffRes',
	'NestOpGroupBuffRes',
	'NestOpComputerBuffRes',
	'NestOpSMBShareBuffRes',
	'NestOpTargetRes',
	'NestOpListTarget',
	'NestOpAddTarget',
	'NestOpCredRes',
	'NestOpListCred',
	'NestOpAddCred',
	'NestOpCredRes',
	'NestOpGetTarget',
	'NestOpLoadGraph',
	'NestOpListGraphRes',
	'NestOpListGraph',
	'NestOpAgent',
	'NestOpListAgents',
	'NestOpWSNETRouterconnect',
	'NestOpWSNETRouterdisconnect',
	'NestOpWSNETRouter',
	'NestOpWSNETListRouters',
	'NestOpSMBFiles',
	'NestOpSMBFileRes',
	'NestOpSMBDCSync',
	'NestOpCredsDef',
	'NestOpTargetDef',
	'NestOpPathKerbroast',
	'NestOpPathASREPRoast',
	'NestOpPathOwned',
	'NestOpObjOwned',
	'NestOpObjHVT',
	'NestOpRDPConnect',
	'NestOpRDPRectangle',
	'NestOpRDPMouse',
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
	NestOpCmd.ASREPROAST : NestOpASREPRoast,
	NestOpCmd.KERBEROASTRES : NestOpKerberoastRes,
	NestOpCmd.ASREPROASTRES : NestOpASREPRoastRes,
	NestOpCmd.KERBEROSTGS : NestOpKerberosTGS, 
	NestOpCmd.KERBEROSTGSRES : NestOpKerberosTGSRes,
	NestOpCmd.KERBEROSTGT : NestOpKerberosTGT,
	NestOpCmd.KERBEROSTGTRES : NestOpKerberosTGTRes,
	NestOpCmd.SMBSESSIONS : NestOpSMBSessions,
	NestOpCmd.SMBDCSYNC : NestOpSMBDCSync,
	NestOpCmd.PATHSHORTEST : NestOpPathShortest,
	NestOpCmd.PATHDA : NestOpPathDA,
	NestOpCmd.GETOBJINFO : NestOpGetOBJInfo,
	NestOpCmd.CHANGEAD : NestOpChangeAD,
	NestOpCmd.LISTADS : NestOpListAD,
	NestOpCmd.OK : NestOpOK,
	NestOpCmd.ERR : NestOpErr,
	NestOpCmd.LOG : NestOpLog,
	NestOpCmd.CANCEL: NestOpCancel,
	NestOpCmd.LISTGRAPHS : NestOpListGraph,
	NestOpCmd.LISTGRAPHRES: NestOpListGraphRes,
	NestOpCmd.CHANGEGRAPH : NestOpChangeGraph,
	NestOpCmd.TCPSCAN: NestOpTCPScan,
	NestOpCmd.TCPSCANRES: NestOpTCPScanRes,
	NestOpCmd.LISTADSRES: NestOpListADRes,
	NestOpCmd.PATHRES: NestOpPathRes,
	NestOpCmd.GATHERSTATUS: NestOpGatherStatus,
	NestOpCmd.USERRES: NestOpUserRes,
	NestOpCmd.SMBSESSIONRES: NestOpSMBSessionRes,
	NestOpCmd.SMBSHARERES: NestOpSMBShareRes,
	NestOpCmd.SMBLOCALGROUPRES: NestOpSMBLocalGroupRes,
	#NestOpCmd.LOADAD: NestOpLoadAD,
	NestOpCmd.EDGERES : NestOpEdgeRes,
	NestOpCmd.LISTTARGET : NestOpListTarget,
	NestOpCmd.LISTCRED : NestOpListCred,
	NestOpCmd.ADDCRED : NestOpAddCred,
	NestOpCmd.ADDTARGET : NestOpAddTarget,
	NestOpCmd.LOADGRAPH : NestOpLoadGraph,
	#NestOpCmd.EDGERES : NestOpEdgeRes,
	#NestOpCmd.EDGERES : NestOpEdgeRes,
	NestOpCmd.LISTAGENTS : NestOpListAgents,
	NestOpCmd.AGENT : NestOpAgent,
	NestOpCmd.COMPUTERRES : NestOpComputerRes,
	NestOpCmd.GROUPRES : NestOpGroupRes,
	NestOpCmd.COMPUTERBUFFRES : NestOpComputerBuffRes,
	NestOpCmd.USERBUFFRES : NestOpUserBuffRes,
	NestOpCmd.GROUPBUFFRES : NestOpGroupBuffRes,
	NestOpCmd.EDGEBUFFRES : NestOpEdgeBuffRes,
	NestOpCmd.WSNETROUTERCONNECT : NestOpWSNETRouterconnect,
	NestOpCmd.WSNETROUTERDISCONNECT : NestOpWSNETRouterdisconnect,
	NestOpCmd.WSNETROUTER: NestOpWSNETRouter,
	NestOpCmd.WSNETLISTROUTERS : NestOpWSNETListRouters,
	NestOpCmd.SMBFILES : NestOpSMBFiles,
	NestOpCmd.SMBFILERES : NestOpSMBFileRes,
	NestOpCmd.PATHKERB : NestOpPathKerbroast,
	NestOpCmd.PATHASREP : NestOpPathASREPRoast,
	NestOpCmd.PATHOWNED : NestOpPathOwned,
	NestOpCmd.OBJOWNED : NestOpObjOwned,
	NestOpCmd.OBJHVT : NestOpObjHVT,
	NestOpCmd.CREDRES : NestOpCredRes,
	NestOpCmd.TARGETRES : NestOpTargetRes,
	NestOpCmd.RDPCONNECT : NestOpRDPConnect,
	NestOpCmd.RDPRECT : NestOpRDPRectangle,
	NestOpCmd.RDPMOUSE : NestOpRDPMouse,
}

