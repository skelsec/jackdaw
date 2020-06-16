#!/usr/bin/env python3
#
# Author:
#  Tamas Jos (@skelsec)
#

import multiprocessing as mp
import threading
import enum
import gzip
import json

from sqlalchemy import func
from sqlalchemy import not_, and_, or_, case
from sqlalchemy.orm import load_only
import networkx as nx
from networkx.readwrite import json_graph

from jackdaw.dbmodel import get_session
from jackdaw.dbmodel.spnservice import SPNService
from jackdaw.dbmodel.adsd import JackDawSD
from jackdaw.dbmodel.adgroup import Group
from jackdaw.dbmodel.adinfo import ADInfo
from jackdaw.dbmodel.aduser import ADUser
from jackdaw.dbmodel.adcomp import Machine
from jackdaw.dbmodel.adou import ADOU
from jackdaw.dbmodel.adinfo import ADInfo
from jackdaw.dbmodel.adtrust import ADTrust
from jackdaw.dbmodel.adgpo import GPO
from jackdaw.dbmodel.constrained import MachineConstrainedDelegation
from jackdaw.dbmodel.adgplink import Gplink
from jackdaw.dbmodel.adspn import JackDawSPN
from jackdaw.dbmodel.netsession import NetSession
from jackdaw.dbmodel.localgroup import LocalGroup
from jackdaw.dbmodel.credential import Credential
from jackdaw.wintypes.well_known_sids import get_name_or_sid, get_sid_for_name
from jackdaw.wintypes.lookup_tables import *
from jackdaw.nest.graph.graphdata import *
from jackdaw import logger
from jackdaw.utils.encoder import UniversalEncoder
from winacl.dtyp.security_descriptor import SECURITY_DESCRIPTOR
import base64
from tqdm import tqdm
from jackdaw.dbmodel import windowed_query

from jackdaw.nest.graph.construct import GraphConstruct
class GraphDecoder(json.JSONDecoder):
	def __init__(self, *args, **kwargs):
		json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)
	def object_hook(self, dct):
		if 'construct' in dct:
			dct['construct'] = GraphConstruct.from_dict(dct['construct'])
		return dct


def ace_applies(ace_guid, object_class):
	'''
	Checks if an ACE applies to this object (based on object classes).
	Note that this function assumes you already verified that InheritedObjectType is set (via the flag).
	If this is not set, the ACE applies to all object types.
	'''
	try:
		our_ace_guid = OBJECTTYPE_GUID_MAP[object_class]
	except KeyError:
		return False
	if ace_guid == our_ace_guid:
		return True
	# If none of these match, the ACE does not apply to this object
	return False

class NodeType(enum.Enum):
	USER = 'USER'
	GROUP = 'GROUP'
	MACHINE = 'MACHINE'
	
class EdgeType(enum.Enum):
	MEMBER_GROUP = 'MEMBER_GROUP'
	MEMBER_USER = 'MEMBER_USER'
	SESSION = 'SESSION'
	ACL = 'ACL'
	LOCALGROUP = 'LOCALGROUP'
	PWSHARE = 'PWSHARE'
	CUSTOM = 'CUSTOM'
	DELEGATION_CONSTRAINED = 'DELEGATION_CONSTRAINED'
	DELEGATION_UNCONSTRAINED = 'DELEGATION_UNCONSTRAINED'

def short_node_gen(graph, inqueue, dst_sid, procno):
	"""
	Adding all nodes from the graph to the inqueue. At the end it adds terminating object in the amount of proccount.
	This function will be threaded. 
	"""
	for node in graph.nodes:
		if node == dst_sid:
			continue
		inqueue.put(node)
			
	for _ in range(procno):
		inqueue.put(None)

def short_worker(inqueue, outqueue, graph, dst_sid):
	"""
	Calculates the shortest parth for a given destination node
	This function is "multiprocessed"
	"""
	while True:
		node = inqueue.get()
		if node is None:
			outqueue.put(None)
			return
		try:
			for path in nx.all_shortest_paths(graph, source = node, target = dst_sid):
				outqueue.put(path)
									
		except nx.exception.NetworkXNoPath:
			continue
		

class DomainGraph:
	def __init__(self, db_conn = None, dbsession = None, db = None):
		self.db_conn = db_conn
		self.db = db
		self.dbsession = dbsession
		self.constructs = {}
		self.graph = nx.DiGraph()
		self.domain_sid = None

	def to_gzip(self, filename = 'test.gzip'):
		gd = json_graph.node_link_data(self.graph)
		gd['domain_sid'] = self.domain_sid

		with gzip.open(filename, 'wt', encoding="utf-8") as zipfile:
			json.dump(gd, zipfile, cls = UniversalEncoder)
	
	@staticmethod
	def from_gzip_stream(stream):
		domain_graph = DomainGraph()
		with gzip.GzipFile(fileobj=stream, mode='r') as zipfile:
			gd = json.load(zipfile, cls=GraphDecoder)
		#print(gd)
		domain_graph.domain_sid = gd['domain_sid']
		del gd['domain_sid']
		domain_graph.graph = json_graph.node_link_graph(gd)

		return domain_graph


	def get_session(self):
		if self.db_conn is not None:
			return get_session(self.db_conn)
		elif self.dbsession is not None:
			return self.dbsession
		elif self.db is not None:
			return self.db.session
		else:
			raise Exception('Either db_conn or dbsession MUST be supplied!')

	######################################################################################################################################
	#################################################      PATH CALCULATION PART         #################################################
	######################################################################################################################################
			
	def sid2cn(self, sid, throw = False):
		session = self.get_session()
		tsid = session.query(Group.cn).filter(Group.sid == sid).first()
		if tsid is not None:
			return tsid[0]
		
		tsid = session.query(ADUser.cn).filter(ADUser.objectSid == sid).first()
		if tsid is not None:
			return tsid[0]
		
		tsid = session.query(Machine.cn).filter(Machine.objectSid == sid).first()
		if tsid is not None:
			return tsid[0]

		tsid = session.query(ADTrust.cn).filter(ADTrust.securityIdentifier == sid).first()
		if tsid is not None:
			return tsid[0]

		
		t = str(get_name_or_sid(str(sid)))
		if t == sid and throw == True:
			raise Exception('No CN found for SID = %s' % repr(sid))
		return t
	
	def cn2sid(self, cn, throw = False, domain_sid = None):
		sid = get_sid_for_name(cn, domain_sid)
		
		session = self.get_session()
		tsid = session.query(Group.objectSid).filter(Machine.cn == cn).first()
		if tsid is not None:
			return tsid[0]
		
		tsid = session.query(ADUser.objectSid).filter(ADUser.cn == cn).first()
		if tsid is not None:
			return tsid[0]
		
		tsid = session.query(Machine.objectSid).filter(Machine.cn == cn).first()
		if tsid is not None:
			return tsid[0]

		tsid = session.query(ADTrust.securityIdentifier).filter(ADTrust.cn == cn).first()
		if tsid is not None:
			return tsid[0]
		
		if throw == True:
			raise Exception('No SID found for CN = %s' % repr(cn))
		return cn
			
	def show_all(self):
		"""
		Returns all nodes and edges from the graph
		You really don't want this on a larger graph, mostly used for testing purposes
		"""
		data = GraphData()
		for sid in self.graph.nodes:
			data.add_node(
				sid, 
				self.graph.nodes[sid].get('name', self.sid2cn(sid)), 
				self.graph.nodes[sid]['construct'].ad_id,
				self.graph.nodes[sid].get('node_type')
			)

		for edge in [e for e in self.graph.edges]:
			data.add_edge(edge[0], edge[1])

		return data
	
	def get_node(self, nodeid = None):
		
		if nodeid is None:
			nodes = []
			for gid, props in list(self.graph.nodes(data=True)):
				nodes.append(GraphNode(gid, gid, props['construct'].ad_id )) #properties = {}))
			return nodes

		if nodeid not in self.graph.nodes:
			return None
		gid, props = self.graph.nodes[nodeid]
		return GraphNode(gid, gid, props['construct'].ad_id, properties = {})
			
	def __add_path(self, network, path):
		"""
		Adds the path to the representational network
		Path is a list of sids (nodes), so we need to find the edges matching
		"""
		for d, sid in enumerate(path):
			network.add_node(
				sid, 
				name = self.graph.nodes[sid].get('name', self.sid2cn(sid)), 
				node_type = self.graph.nodes[sid].get('node_type'),
				domainid = self.graph.nodes[sid]['construct'].ad_id
			)
			network.nodes[sid].set_distance(d)
		
		for i in range(len(path) - 1):
			for edge in self.graph.edges([path[i], ], data=True):
				if edge[1] == path[i + 1]:
					name = edge[2].get('label', None)
					network.add_edge(path[i], path[i + 1], label=name)

	def distances_from_node(self, dst_sid):
		
		distances = {} #distance -> occurrence of distance
		for node in self.graph.nodes:
			try:
				for path in nx.all_shortest_paths(self.graph, source = node, target = dst_sid):
					distance = len(path)
					if distance not in distances:
						distances[distance] = 0
					distances[distance] += 1
			except nx.exception.NetworkXNoPath:
				continue

		return distances

	def all_shortest_paths(self, src_sid = None, dst_sid = None):
		nv = GraphData()
		
		if not src_sid and not dst_sid:
			raise Exception('Either source or destination MUST be specified')
		
		elif not src_sid and dst_sid:
			try:
				#for each node we calculate the shortest path to the destination node, silently skip the ones who do not have path to dst
				inqueue = mp.Queue()
				outqueue = mp.Queue()
				procno = mp.cpu_count()
				logger.debug('[DST_CALC] Starting processes')
				procs = [mp.Process(target = short_worker, args = (inqueue, outqueue, self.graph, dst_sid)) for i in range(procno)]			
				for proc in procs:
					proc.daemon = True
					proc.start()
				logger.debug('[DST_CALC] Starting generator thread')
				node_gen_th = threading.Thread(target = short_node_gen, args = (self.graph, inqueue, dst_sid, procno))
				node_gen_th.daemon = True
				node_gen_th.start()

				p_cnt = 0
				while True:
					path = outqueue.get()
					if path is None:
						procno -= 1
						logger.debug('[DST_CALC] Proc X - Finished!')
						if procno == 0:
							break
						continue
					self.__add_path(nv, path)
					p_cnt += 1

				logger.debug('[DST_CALC] Found %s paths to dst node %s' % (p_cnt, dst_sid))

				logger.debug('[DST_CALC] joining processes')
				for proc in procs:
					proc.join()
				logger.debug('[DST_CALC] Finished!')

			except:
				logger.exception('[DST_CALC]')
			
		elif src_sid and not dst_sid:
			#for each node we calculate the shortest path to the destination node, silently skip the ones who do not have path to dst
			
			for node in self.graph.nodes:
				if node == src_sid:
					continue
				try:
					for path in nx.all_shortest_paths(self.graph, source = src_sid, target = node):
						self.__add_path(nv, path)
									
				except nx.exception.NetworkXNoPath:
					continue
					
		else:
			#for each node we calculate the shortest path to the destination node, silently skip the ones who do not have path to dst
			for path in nx.all_shortest_paths(self.graph, source = src_sid, target = dst_sid):
				self.__add_path(nv, path)
		
		return nv
	
	####################################################################################################
	#####################################################################################################

	def add_sid_to_node(self, node, node_type, construct, name = None):
		if construct.is_blacklisted_sid(node):
			return
		if not name:
			name = str(get_name_or_sid(str(node)))
		
		#this presence-filter is important, as we will encounter nodes that are known and present in the graph already
		#ald later will be added via tokengroups as unknown
		if node not in self.graph.nodes:
			self.graph.add_node(str(node), name=name, node_type=node_type, construct = construct)
		
			
	def add_edge(self, sid_src, sid_dst, construct, label = None, weight = 1):
		if not sid_src or not sid_dst:
			return
		if construct.is_blacklisted_sid(sid_src) or construct.is_blacklisted_sid(sid_dst):
			return
			
		self.add_sid_to_node(sid_src, 'unknown', construct)
		self.add_sid_to_node(sid_dst, 'unknown', construct)
			
		self.graph.add_edge(sid_src, sid_dst, label = label, weight = weight)
		
		#self.network_visual.add_edge(sid_src, sid_dst, label = label, weight = weight)

	def construct(self, construct):
		"""
		Fills the network graph from database to memory
		"""
		#self.ad_id = ad_id
		session = self.get_session()
		adinfo = session.query(ADInfo).get(construct.ad_id)
		
		self.domain_sid = str(adinfo.objectSid)

		#adding group nodes
		logger.debug('Adding group nodes')
		cnt = 0
		for group in adinfo.groups:
			self.add_sid_to_node(group.sid, 'group', construct, name=group.name)
			cnt += 1
		
		logger.debug('Added %s group nodes' % cnt)
		
		logger.debug('Adding user nodes')
		cnt = 0
		for user in adinfo.users:
			self.add_sid_to_node(user.objectSid, 'user', construct, name=user.sAMAccountName)
			cnt += 1
		
		logger.debug('Added %s user nodes' % cnt)
				
		logger.debug('Adding machine nodes')
		cnt = 0
		for user in adinfo.computers:
			self.add_sid_to_node(user.objectSid, 'machine', construct, name=user.sAMAccountName)
			cnt += 1
		logger.debug('Added %s machine nodes' % cnt)

		output_file_path = 'test.csv'
		calc = EdgeCalc(
			session, 
			adinfo.id, 
			output_file_path, 
			buffer_size = 100, 
			dst_ad_id = None, 
			show_progress = False, 
			progress_queue = None, 
			append_to_file = False, 
			worker_count = None
		)
		calc.run()

		cnt = 0
		with open(output_file_path,'r') as f:
			for line in f:
				line = line.strip()
				src, dst, label, adid = line.split(',')
				self.add_edge(src, dst, construct, label = label)
				cnt += 1

		logger.info('Done! %s' % cnt)