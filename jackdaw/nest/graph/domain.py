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
from jackdaw.dbmodel.spnservice import JackDawSPNService
from jackdaw.dbmodel.addacl import JackDawADDACL
from jackdaw.dbmodel.adsd import JackDawSD
from jackdaw.dbmodel.adgroup import JackDawADGroup
from jackdaw.dbmodel.adinfo import JackDawADInfo
from jackdaw.dbmodel.aduser import JackDawADUser
from jackdaw.dbmodel.adcomp import JackDawADMachine
from jackdaw.dbmodel.adou import JackDawADOU
from jackdaw.dbmodel.usergroup import JackDawGroupUser
from jackdaw.dbmodel.adinfo import JackDawADInfo
from jackdaw.dbmodel.tokengroup import JackDawTokenGroup
from jackdaw.dbmodel.adgpo import JackDawADGPO
from jackdaw.dbmodel.constrained import JackDawMachineConstrainedDelegation, JackDawUserConstrainedDelegation
from jackdaw.dbmodel.adgplink import JackDawADGplink
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

from jackdaw.nest.graph.construct import GraphConstruct
class GraphDecoder(json.JSONDecoder):
	def __init__(self, *args, **kwargs):
		json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)
	def object_hook(self, dct):
		if 'construct' in dct:
			dct['construct'] = GraphConstruct.from_dict(dct['construct'])
		return dct

def windowed_query(q, column, windowsize, is_single_entity = True):
	""""Break a Query into chunks on a given column."""

	#single_entity = q.is_single_entity
	q = q.add_column(column).order_by(column)
	last_id = None

	while True:
		subq = q
		if last_id is not None:
			subq = subq.filter(column > last_id)
		chunk = subq.limit(windowsize).all()
		if not chunk:
			break
		last_id = chunk[-1][-1]
		for row in chunk:
			if is_single_entity is True:
				yield row[0]
			else:
				yield row[0:-1]


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


def acl_calc_gen(session, adid, inqueue, procno):
	total = session.query(func.count(JackDawSD.id)).filter_by(ad_id = adid).scalar()

	q = session.query(JackDawSD).filter_by(ad_id = adid)

	for adsd in tqdm(windowed_query(q, JackDawSD.id, 1000), total=total):
		sd = SECURITY_DESCRIPTOR.from_bytes(base64.b64decode(adsd.sd))
		
		order_ctr = 0
		for ace in sd.Dacl.aces:
			acl = JackDawADDACL()
			acl.ad_id = adsd.ad_id
			acl.object_type = adsd.object_type
			acl.object_type_guid = OBJECTTYPE_GUID_MAP.get(adsd.object_type)
			acl.owner_sid = str(sd.Owner)
			acl.group_sid = str(sd.Group)
			acl.ace_order = order_ctr
			
			order_ctr += 1
			acl.guid = str(adsd.guid)
			if adsd.sid:
				acl.sid = str(adsd.sid)
			#if sd.cn:
			#	acl.cn = sd.cn
			#if sd.distinguishedName:
			#	acl.dn = str(sd.distinguishedName)
			acl.sd_control = sd.Control
			
			acl.ace_type = ace.AceType.name
			acl.ace_mask = ace.Mask
			t = getattr(ace,'ObjectType', None)
			if t:
				acl.ace_objecttype = str(t)
			
			t = getattr(ace,'InheritedObjectType', None)
			if t:
				acl.ace_inheritedobjecttype = str(t)
				
			true_attr, false_attr = JackDawADDACL.mask2attr(ace.Mask)
			
			for attr in true_attr:	
				setattr(acl, attr, True)
			for attr in false_attr:	
				setattr(acl, attr, False)
				
			true_attr, false_attr = JackDawADDACL.hdrflag2attr(ace.AceFlags)
			
			for attr in true_attr:	
				setattr(acl, attr, True)
			for attr in false_attr:	
				setattr(acl, attr, False)
			
			acl.ace_sid = str(ace.Sid)
		
			inqueue.put(acl)
	#adinfo = session.query(JackDawADInfo).get(adid)
	#for acl in adinfo.objectacls:
	#	inqueue.put(acl)

	for _ in range(procno):
		inqueue.put(None)

def acl_calc_mp(inqueue, outqueue, construct):
	while True:
		acl = inqueue.get()
		if acl is None:
			outqueue.put(None)
			return
		
		if acl.owner_sid not in construct.ignoresids:
			outqueue.put((acl.owner_sid, acl.sid, 'Owner'))
				
		if acl.ace_sid in construct.ignoresids:
			continue
			
		if acl.ace_type not in ['ACCESS_ALLOWED_ACE_TYPE','ACCESS_ALLOWED_OBJECT_ACE_TYPE']:
			continue

		if acl.ace_type == 'ACCESS_ALLOWED_ACE_TYPE':
			if acl.ace_mask_generic_all == True:
				outqueue.put((acl.ace_sid, acl.sid, 'GenericALL'))
			
			if acl.ace_mask_generic_write == True:
				outqueue.put((acl.ace_sid, acl.sid, 'GenericWrite'))
				
			if acl.ace_mask_write_owner == True:
				outqueue.put((acl.ace_sid, acl.sid, 'WriteOwner'))
				
			if acl.ace_mask_write_dacl == True:
				outqueue.put((acl.ace_sid, acl.sid, 'WriteDacl'))
				
			if acl.object_type in ['user', 'domain'] and acl.ace_mask_control_access == True:
				outqueue.put((acl.ace_sid, acl.sid, 'ExtendedRightALL'))
		
		if acl.ace_type == 'ACCESS_ALLOWED_OBJECT_ACE_TYPE':
			if acl.ace_hdr_flag_inherited == True and acl.ace_hdr_flag_inherit_only == True:
				continue
			
			if acl.ace_hdr_flag_inherited == True and acl.ace_inheritedobjecttype is not None:
				if not ace_applies(acl.ace_inheritedobjecttype, acl.object_type):
					continue
			
			if any([acl.ace_mask_generic_all, acl.ace_mask_write_dacl, acl.ace_mask_write_owner, acl.ace_mask_generic_write]):
				if acl.ace_objecttype is not None and not ace_applies(acl.ace_objecttype, acl.object_type):
					continue
				
				if acl.ace_mask_generic_all == True:
					outqueue.put((acl.ace_sid, acl.sid, 'GenericALL'))
					continue
		
				if acl.ace_mask_generic_write == True:
					outqueue.put((acl.ace_sid, acl.sid, 'GenericWrite'))
					if acl.object_type != 'domain':
						continue
					
				if acl.ace_mask_write_dacl == True:
					outqueue.put((acl.ace_sid, acl.sid, 'WriteDacl'))
					
				if acl.ace_mask_write_owner == True:
					outqueue.put((acl.ace_sid, acl.sid, 'WriteOwner'))
					
			if acl.ace_mask_write_prop == True:
				if acl.object_type in ['user','group'] and acl.ace_objecttype is None:
					outqueue.put((acl.ace_sid, acl.sid, 'GenericWrite'))
					
				if acl.object_type == 'group' and acl.ace_objecttype == 'bf9679c0-0de6-11d0-a285-00aa003049e2':
					outqueue.put((acl.ace_sid, acl.sid, 'AddMember'))
					
				
		
			if acl.ace_mask_control_access == True:
				if acl.object_type in ['user','group'] and acl.ace_objecttype is None:
					outqueue.put((acl.ace_sid, acl.sid, 'ExtendedAll'))
				
				if acl.object_type == 'domain' and acl.ace_objecttype == '1131f6ad-9c07-11d1-f79f-00c04fc2dcd2':
					# 'Replicating Directory Changes All'
					outqueue.put((acl.ace_sid, acl.sid, 'GetChangesALL'))
						
				if acl.object_type == 'domain' and acl.ace_objecttype == '1131f6aa-9c07-11d1-f79f-00c04fc2dcd2':
					# 'Replicating Directory Changes'
					outqueue.put((acl.ace_sid, acl.sid, 'GetChanges'))
						
				if acl.object_type == 'user' and acl.ace_objecttype == '00299570-246d-11d0-a768-00aa006e0529':
					# 'Replicating Directory Changes'
					outqueue.put((acl.ace_sid, acl.sid, 'User-Force-Change-Password'))
		

class DomainGraph:
	def __init__(self, db_conn = None, dbsession = None):
		self.db_conn = db_conn
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
		else:
			raise Exception('Either db_conn or dbsession MUST be supplied!')

	######################################################################################################################################
	#################################################      PATH CALCULATION PART         #################################################
	######################################################################################################################################
			
	def sid2cn(self, sid, throw = False):
		session = self.get_session()
		tsid = session.query(JackDawTokenGroup.cn).filter(JackDawTokenGroup.sid == sid).first()
		#print('sid2cn: %s' % tsid)
		if not tsid:
			t = str(get_name_or_sid(str(sid)))
			if t == sid and throw == True:
				raise Exception('No CN found for SID = %s' % repr(sid))
			return t
		return tsid[0]
	
	def cn2sid(self, cn, throw = False, domain_sid = None):
		sid = get_sid_for_name(cn, domain_sid)
		
		session = self.get_session()
		tsid = session.query(JackDawTokenGroup.sid).filter(JackDawTokenGroup.cn == cn).first()
		#print(tsid)
		if not tsid:
			if throw == True:
				raise Exception('No SID found for CN = %s' % repr(cn))
			return cn
		return tsid[0]
			
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
	

	######################################################################################################################################
	#################################################      GRAPH CALCULATION PART        #################################################
	######################################################################################################################################

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


	def calc_acl_edges_mp(self, session, adid, construct):
		try:
			#ACE edges calc with multiprocessing
			inqueue = mp.Queue()
			outqueue = mp.Queue()
			procno = mp.cpu_count()
			logger.debug('[ACL] Starting processes')
			procs = [mp.Process(target = acl_calc_mp, args = (inqueue, outqueue, construct)) for i in range(procno)]			
			for proc in procs:
				proc.daemon = True
				proc.start()
			logger.debug('[ACL] Starting generator thread')
			acl_gen_th = threading.Thread(target = acl_calc_gen, args = (session, adid, inqueue, procno))
			acl_gen_th.daemon = True
			acl_gen_th.start()

			p_cnt = 0
			while True:
				res = outqueue.get()
				if res is None:
					procno -= 1
					logger.debug('[ACL] Proc X - Finished!')
					if procno == 0:
						break
					continue
				ace_sid, sid, label = res
				self.add_edge(ace_sid, sid, construct, label=label)
				p_cnt += 1

			logger.debug('[ACL] Added %s edges' % (p_cnt))

			logger.debug('[ACL] joining processes')
			for proc in procs:
				proc.join()
			logger.debug('[ACL] Finished!')

		except:
			logger.exception('[ACL]')
	
	def calc_acl_edges(self, session, construct):
		logger.debug('Adding ACL edges - single thread')
		cnt = 0
		q = session.query(JackDawADDACL).filter_by(ad_id = construct.ad_id)

		for acl in windowed_query(q, JackDawADDACL.id, 1000):
			#input(acl[0])
			#acl = acl[0]
			#cnt += 1
			#if cnt % 10000 == 0:
			#	print(cnt)
			#continue
			##SUPER-IMPORTANT!!!!
			##THE ACCESS RIGHTS CALCULATIONS ARE FLAWED (JUST LIKE IN BLOODHOUND)
			##CORRECT WAY WOULD BE TO TRAVERSE ALL ACES IN A GIVEN ACL IN THE ORDER OF "ACE-ODER" AND CHECK FOR DENY POLICIES AS WELL!!!
			##TODO: CALCULATE THE EFFECTIVE PERMISSIONS IN A CORRECT MANNER :)
			
			##TODO: The DB is designed that most of these calculations can (and should) be offloaded to the DB itself
			##      Currently it's in python bc I'm laze and Dirkjan already wrote the major part
			##      https://github.com/fox-it/BloodHound.py/blob/0d3897ba4cc00818c0fc3e01fa3a91fc42e799e2/bloodhound/enumeration/acls.py
			
			if acl.owner_sid not in construct.ignoresids:
				self.add_edge(acl.owner_sid, acl.sid, construct, label='Owner')
				
			if acl.ace_sid in construct.ignoresids:
				continue
			
			if acl.ace_type in ['ACCESS_ALLOWED_ACE_TYPE','ACCESS_ALLOWED_OBJECT_ACE_TYPE']:
				if acl.ace_type == 'ACCESS_ALLOWED_ACE_TYPE':
					if acl.ace_mask_generic_all == True:
						self.add_edge(acl.ace_sid, acl.sid, construct, label='GenericALL')
						cnt += 1
					
					if acl.ace_mask_generic_write == True:
						self.add_edge(acl.ace_sid, acl.sid, construct, label='GenericWrite')
						cnt += 1
						
					if acl.ace_mask_write_owner == True:
						self.add_edge(acl.ace_sid, acl.sid, construct, label='WriteOwner')
						cnt += 1
						
					if acl.ace_mask_write_dacl == True:
						self.add_edge(acl.ace_sid, acl.sid, construct, label='WriteDacl')
						cnt += 1
						
					if acl.object_type in ['user', 'domain'] and acl.ace_mask_control_access == True:
						self.add_edge(acl.ace_sid, acl.sid, construct, label='ExtendedRightALL')
						cnt += 1
				
				if acl.ace_type == 'ACCESS_ALLOWED_OBJECT_ACE_TYPE':
					if acl.ace_hdr_flag_inherited == True and acl.ace_hdr_flag_inherit_only == True:
						continue
					
					if acl.ace_hdr_flag_inherited == True and acl.ace_inheritedobjecttype is not None:
						if not ace_applies(acl.ace_inheritedobjecttype, acl.object_type):
							continue
					
					if any([acl.ace_mask_generic_all, acl.ace_mask_write_dacl, acl.ace_mask_write_owner, acl.ace_mask_generic_write]):
						if acl.ace_objecttype is not None and not ace_applies(acl.ace_objecttype, acl.object_type):
							continue
						
						if acl.ace_mask_generic_all == True:
							self.add_edge(acl.ace_sid, acl.sid, construct, label='GenericALL')
							cnt += 1
							continue
				
						if acl.ace_mask_generic_write == True:
							self.add_edge(acl.ace_sid, acl.sid, construct, label='GenericWrite')
							cnt += 1
							if acl.object_type != 'domain':
								continue
							
						if acl.ace_mask_write_dacl == True:
							self.add_edge(acl.ace_sid, acl.sid, construct, label='WriteDacl')
							cnt += 1
							
						if acl.ace_mask_write_owner == True:
							self.add_edge(acl.ace_sid, acl.sid, construct, label='WriteOwner')
							cnt += 1
							
					if acl.ace_mask_write_prop == True:
						if acl.object_type in ['user','group'] and acl.ace_objecttype is None:
							self.add_edge(acl.ace_sid, acl.sid, construct, label='GenericWrite')
							cnt += 1
							
						if acl.object_type == 'group' and acl.ace_objecttype == 'bf9679c0-0de6-11d0-a285-00aa003049e2':
							self.add_edge(acl.ace_sid, acl.sid, construct, label='AddMember')
							cnt += 1
							
						
				
					if acl.ace_mask_control_access == True:
						if acl.object_type in ['user','group'] and acl.ace_objecttype is None:
							self.add_edge(acl.ace_sid, acl.sid, construct, label='ExtendedAll')
							cnt += 1
						
						if acl.object_type == 'domain' and acl.ace_objecttype == '1131f6ad-9c07-11d1-f79f-00c04fc2dcd2':
							# 'Replicating Directory Changes All'
							self.add_edge(acl.ace_sid, acl.sid, construct, label='GetChangesALL')
							cnt += 1
								
						if acl.object_type == 'domain' and acl.ace_objecttype == '1131f6aa-9c07-11d1-f79f-00c04fc2dcd2':
							# 'Replicating Directory Changes'
							self.add_edge(acl.ace_sid, acl.sid, construct, label='GetChanges')
							cnt += 1
								
						if acl.object_type == 'user' and acl.ace_objecttype == '00299570-246d-11d0-a768-00aa006e0529':
							# 'Replicating Directory Changes'
							self.add_edge(acl.ace_sid, acl.sid, construct, label='User-Force-Change-Password')
							cnt += 1
		
		logger.debug('Added %s ACL edges' % cnt)

	def construct(self, construct):
		"""
		Fills the network graph from database to memory
		"""
		#self.ad_id = ad_id
		session = self.get_session()
		adinfo = session.query(JackDawADInfo).get(construct.ad_id)
		
		self.domain_sid = str(adinfo.objectSid)

		#self.calc_acl_edges(session, construct)

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

		logger.debug('Adding hassession edges')
		cnt = 0
		for res in session.query(JackDawADUser.objectSid, JackDawADMachine.objectSid).filter(NetSession.username == JackDawADUser.sAMAccountName).filter(NetSession.source == JackDawADMachine.sAMAccountName).distinct(NetSession.username):
			self.add_edge(res[0], res[1], construct, label='hasSession')
			self.add_edge(res[1], res[0], construct, label='hasSession')
			cnt += 2
		logger.debug('Added %s hassession edges' % cnt)
		
		logger.debug('Adding localgroup edges')
		cnt = 0
		for res in session.query(JackDawADUser.objectSid, JackDawADMachine.objectSid, LocalGroup.groupname
					).filter(JackDawADMachine.id == LocalGroup.machine_id
					).filter(JackDawADMachine.ad_id == construct.ad_id
					).filter(JackDawADUser.ad_id == construct.ad_id
					).filter(JackDawADUser.objectSid == LocalGroup.sid
					).all():
			label = None
			if res[2] == 'Remote Desktop Users':
				label = 'canRDP'
				weight = 1
					
			elif res[2] == 'Distributed COM Users':
				label = 'executeDCOM'
				weight = 1
					
			elif res[2] == 'Administrators':
				label = 'adminTo'
				weight = 1
					
			self.add_edge(res[0], res[1], construct, label=label, weight = weight)
			cnt += 1

		logger.debug('Added %s localgroup edges' % cnt)

		# TODO: implement this!	
		#if self.show_constrained_delegations == True:
		#	pass
			
		# TODO: implement this!	
		#if self.show_unconstrained_delegations == True:
		#	pass

		# TODO: implement this!	
		#for relation in construct.custom_relations:
		#	relation.calc()
		#	self.add_edge(res.sid, res.target_sid)
			
		#print('adding membership edges')
		#adding membership edges
		logger.debug('Adding membership edges')
		cnt = 0

		q = session.query(JackDawTokenGroup).filter_by(ad_id = construct.ad_id)

		for tokengroup in windowed_query(q, JackDawTokenGroup.id, 10000):
		#for tokengroup in adinfo.group_lookups:
			self.add_sid_to_node(tokengroup.sid, 'unknown', construct)
			self.add_sid_to_node(tokengroup.member_sid, 'unknown', construct)
				
			if tokengroup.is_user == True:
				try:
					self.add_edge(tokengroup.sid, tokengroup.member_sid, construct, label='member')
					cnt += 1
				except AssertionError:
					logger.exception()
			elif tokengroup.is_machine == True:
				try:
					self.add_edge(tokengroup.sid, tokengroup.member_sid, construct, label='member')
					cnt += 1
				except AssertionError:
					logger.exception()
			elif tokengroup.is_group == True:
				try:
					self.add_edge(tokengroup.sid, tokengroup.member_sid, construct, label='member')
					cnt += 1
				except AssertionError:
					logger.exception()
		
		logger.debug('Added %s membership edges' % cnt)
		
		#adding ACL edges
		#self.calc_acl_edges(session, construct)
		#self.calc_acl_edges(adinfo, construct)
		self.calc_acl_edges_mp(session, construct.ad_id, construct)

		logger.info('Adding password sharing edges')
		cnt = 0
		def get_sid_by_nthash(ad_id, nt_hash):
			return session.query(JackDawADUser.objectSid, Credential.username
				).filter_by(ad_id = ad_id
				).filter(Credential.username == JackDawADUser.sAMAccountName
				).filter(Credential.nt_hash == nt_hash
				)

		dup_nthashes_qry = session.query(Credential.nt_hash
					).filter(Credential.history_no == 0
					).filter(Credential.ad_id == construct.ad_id
					   ).filter(Credential.username != 'NA'
					   ).filter(Credential.domain != '<LOCAL>'
					).group_by(
						Credential.nt_hash
					).having(
						func.count(Credential.nt_hash) > 1
					)

		for res in dup_nthashes_qry.all():
			sidd = {}
			for sid, _ in get_sid_by_nthash(construct.ad_id, res[0]).all():
				sidd[sid] = 1

			for sid1 in sidd:
				for sid2 in sidd:
					if sid1 == sid2:
						continue
					self.add_edge(sid1, sid2, construct, label = 'pwsharing')
					cnt += 1

		logger.info('Added %s password sharing edges' % cnt)
