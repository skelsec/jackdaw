
from jackdaw.dbmodel.adinfo import JackDawADInfo
from jackdaw.dbmodel.tokengroup import JackDawTokenGroup
from jackdaw.dbmodel import *
from jackdaw.wintypes.well_known_sids import get_name_or_sid, get_sid_for_name
from jackdaw.wintypes.lookup_tables import *
from sqlalchemy import not_, and_, or_, case
from sqlalchemy.orm import load_only
#from pyvis.network import Network
#from pyvis.options import Layout
import networkx as nx

from jackdaw.nest.graph.graphdata import *
from jackdaw import logger
import enum


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


class DomainGraph:
	def __init__(self, db_conn = None, dbsession = None):
		self.db_conn = db_conn
		self.dbsession = dbsession
		self.constructs = {}
		self.graph = nx.DiGraph()

		
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
		#print('PATH: %s' % repr(path))
		for d, sid in enumerate(path):
			#print(sid)
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
			#for each node we calculate the shortest path to the destination node, silently skip the ones who do not have path to dst
			for node in self.graph.nodes:
				if node == dst_sid:
					continue
				try:
					for path in nx.all_shortest_paths(self.graph, source = node, target = dst_sid):
						self.__add_path(nv, path)
									
				except nx.exception.NetworkXNoPath:
					continue
			
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
	
	def calc_acl_edges(self, adinfo, construct):
		for acl in adinfo.objectacls:
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
					
					if acl.ace_mask_generic_write == True:
						self.add_edge(acl.ace_sid, acl.sid, construct, label='GenericWrite')
						
					if acl.ace_mask_write_owner == True:
						self.add_edge(acl.ace_sid, acl.sid, construct, label='WriteOwner')
						
					if acl.ace_mask_write_dacl == True:
						self.add_edge(acl.ace_sid, acl.sid, construct, label='WriteDacl')
						
					if acl.object_type in ['user', 'domain'] and acl.ace_mask_control_access == True:
						self.add_edge(acl.ace_sid, acl.sid, construct, label='ExtendedRightALL')
				
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
							continue
				
						if acl.ace_mask_generic_write == True:
							self.add_edge(acl.ace_sid, acl.sid, construct, label='GenericWrite')
							
							if acl.object_type != 'domain':
								continue
							
						if acl.ace_mask_write_dacl == True:
							self.add_edge(acl.ace_sid, acl.sid, construct, label='WriteDacl')
							
						if acl.ace_mask_write_owner == True:
							self.add_edge(acl.ace_sid, acl.sid, construct, label='WriteOwner')
							
					if acl.ace_mask_write_prop == True:
						if acl.object_type in ['user','group'] and acl.ace_objecttype is None:
							self.add_edge(acl.ace_sid, acl.sid, construct, label='GenericWrite')
							
						if acl.object_type == 'group' and acl.ace_objecttype == 'bf9679c0-0de6-11d0-a285-00aa003049e2':
							self.add_edge(acl.ace_sid, acl.sid, construct, label='AddMember')
							
						
				
					if acl.ace_mask_control_access == True:
						if acl.object_type in ['user','group'] and acl.ace_objecttype is None:
							self.add_edge(acl.ace_sid, acl.sid, construct, label='ExtendedAll')
						
						if acl.object_type == 'domain' and acl.ace_objecttype == '1131f6ad-9c07-11d1-f79f-00c04fc2dcd2':
							# 'Replicating Directory Changes All'
							self.add_edge(acl.ace_sid, acl.sid, construct, label='GetChangesALL')
								
						if acl.object_type == 'domain' and acl.ace_objecttype == '1131f6aa-9c07-11d1-f79f-00c04fc2dcd2':
								# 'Replicating Directory Changes'
								self.add_edge(acl.ace_sid, acl.sid, construct, label='GetChanges')
								
						if acl.object_type == 'user' and acl.ace_objecttype == '00299570-246d-11d0-a768-00aa006e0529':
								# 'Replicating Directory Changes'
								self.add_edge(acl.ace_sid, acl.sid, construct, label='User-Force-Change-Password')
		
	def construct(self, construct):
		"""
		Fills the network graph from database to memory
		"""
		#self.ad_id = ad_id
		session = self.get_session()
		adinfo = session.query(JackDawADInfo).get(construct.ad_id)
		
		self.domain_sid = str(adinfo.objectSid)
	
		#adding group nodes
		for group in adinfo.groups:
			self.add_sid_to_node(group.sid, 'group', construct, name=group.name)
		
		for user in adinfo.users:
			self.add_sid_to_node(user.objectSid, 'user', construct, name=user.sAMAccountName)
				
		#adding user nodes
		for user in adinfo.computers:
			self.add_sid_to_node(user.objectSid, 'machine', construct, name=user.sAMAccountName)
		
		
		for res in session.query(JackDawADUser.objectSid, JackDawADMachine.objectSid).filter(NetSession.username == JackDawADUser.sAMAccountName).filter(NetSession.source == JackDawADMachine.sAMAccountName).distinct(NetSession.username):
			self.add_edge(res[0], res[1], construct, label='hasSession')
			self.add_edge(res[1], res[0], construct, label='hasSession')
		

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
		for tokengroup in adinfo.group_lookups:
			self.add_sid_to_node(tokengroup.sid, 'unknown', construct)
			self.add_sid_to_node(tokengroup.member_sid, 'unknown', construct)
				
			if tokengroup.is_user == True:
				try:
					self.add_edge(tokengroup.sid, tokengroup.member_sid, construct, label='member')
				except AssertionError as e:
					logger.exception()
			elif tokengroup.is_machine == True:
				try:
					self.add_edge(tokengroup.sid, tokengroup.member_sid, construct, label='member')
				except AssertionError as e:
					logger.exception()
			elif tokengroup.is_group == True:
				try:
					self.add_edge(tokengroup.sid, tokengroup.member_sid, construct, label='member')
				except AssertionError as e:
					logger.exception()
		
		logger.info('Adding ACL edges')
		#adding ACL edges
		self.calc_acl_edges(adinfo, construct)


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

		
						
				
					