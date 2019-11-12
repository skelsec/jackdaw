
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
import math
from jackdaw import logger

class GraphNode:
	def __init__(self, gid, name, gtype = None, properties = {}):
		self.name = name
		self.id = gid
		self.type = gtype
		self.properties = properties
		self.mindistance = math.inf

	def set_distance(self, d):
		self.mindistance = min(self.mindistance, d)

	def serialize_mindistance(self):
		if self.mindistance == math.inf:
			return 999999

	def to_dict(self, format = None):
		if format is None:
			return {
				'id' : self.id,
				'name' : self.name,
				'properties' : self.properties,
				'md' : self.serialize_mindistance(),
			}

		elif format == 'd3':
			return {
				'id' : self.id,
				'name' : self.name,
				'type' : self.type,
				'md' : self.serialize_mindistance(),
			}
		
		elif format == 'vis':
			return {
				'id' : self.id,
				'label' : self.name,
				'type' : self.type,
				'md' : self.serialize_mindistance(),
			}

class GraphEdge:
	def __init__(self, src, dst, label = '', weight = 1, properties = {}):
		self.src = src
		self.dst = dst
		self.label = label
		self.weight = weight
		self.properties = properties

	def to_dict(self, format = None):
		if format is None:
			return {
				'src' : self.src,
				'dst' : self.dst,
				'label' : self.label,
				'weight' : self.weight,
				'properties' : self.properties
			}
		elif format == 'd3':
			return {
				'source' : self.src,
				'target' : self.dst,
				'label'  : self.label,
				'weight' : self.weight,
			}
		elif format == 'vis':
			return {
				'from' : self.src,
				'to' : self.dst,
				'label'  : self.label,
				'weight' : self.weight,
			}


class GraphData:
	def __init__(self):
		self.nodes = {}
		self.edges = []

	def add_node(self, gid, name, node_type, properties = {}):
		self.nodes[gid] = GraphNode(gid, name, node_type, properties)
	
	def add_edge(self, src, dst, label = '', weight = 1, properties = {}):
		if src not in self.nodes:
			raise Exception('Node with id %s is not present' % src)
		if dst not in self.nodes:
			raise Exception('Node with id %s is not present' % dst)

		self.edges.append(GraphEdge(src, dst, label, weight, properties))

	def __add__(self, o):
		if not isinstance(o, GraphData):
			raise Exception('Cannot add GraphData and %s' % type(o))
		
		self.nodes.update(o.nodes)
		self.edges += o.edges
		return self

	def to_dict(self, format = None):
		if format is None:
			return {
				'nodes' : [self.nodes[x].to_dict() for x in self.nodes],
				'edges' : [x.to_dict() for x in self.edges]
			}
		elif format == 'd3':
			return {
				'nodes' : [self.nodes[x].to_dict(format = format) for x in self.nodes],
				'links' : [x.to_dict(format = format) for x in self.edges]
			}
		elif format == 'vis':
			return {
				'nodes' : [self.nodes[x].to_dict(format = format) for x in self.nodes],
				'edges' : [x.to_dict(format = format) for x in self.edges]
			}

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


class DomainGraph:
	def __init__(self, db_conn = None, dbsession = None):
		self.db_conn = db_conn
		self.dbsession = dbsession
		self.ad_id = None
		self.graph = nx.DiGraph()
		#self.network_visual = Network("3000px", "3000px")
		self.show_group_memberships = True
		self.show_user_memberships = True
		self.show_machine_memberships = True
		self.show_session_memberships = True
		self.show_localgroup_memberships = False
		self.show_constrained_delegations = True
		self.show_unconstrained_delegations = True
		self.show_custom_relations = True
		self.show_acl = True
		self.unknown_node_color = "#ffffff"
		self.domain_sid = None
		
		self.blacklist_sids = {'S-1-5-32-545': ''}
		self.ignoresids = {"S-1-3-0": '', "S-1-5-18": ''}

	def get_session(self):
		if self.db_conn is not None:
			return get_session(self.db_conn)
		elif self.dbsession is not None:
			return self.dbsession
		else:
			raise Exception('Either db_conn or dbsession MUST be supplied!')
		
	def is_blacklisted_sid(self, sid):
		if sid in self.blacklist_sids:
			return True
		if sid[:len('S-1-5-21')] == 'S-1-5-21':
			if sid[-3:] == '513':
				return True
			
		return False
	
	def add_sid_to_node(self, node, node_type, name = None):
		if self.is_blacklisted_sid(node):
			return
		if not name:
			name = str(get_name_or_sid(str(node)))
		
		#this presence-filter is important, as we will encounter nodes that are known and present in the graph already
		#ald later will be added via tokengroups as unknown
		if node not in self.graph.nodes:
			self.graph.add_node(str(node), name=name, node_type=node_type)
		
			
	def add_edge(self, sid_src, sid_dst, label = None, weight = 1):
		if not sid_src or not sid_dst:
			return
		if self.is_blacklisted_sid(sid_src) or self.is_blacklisted_sid(sid_dst):
			return
			
		self.add_sid_to_node(sid_src, 'unknown')
		self.add_sid_to_node(sid_dst, 'unknown')
			
		self.graph.add_edge(sid_src, sid_dst, label = label, weight = weight)
		
		#self.network_visual.add_edge(sid_src, sid_dst, label = label, weight = weight)
			
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
			data.add_node(sid, self.graph.nodes[sid].get('name', self.sid2cn(sid)), self.graph.nodes[sid].get('node_type'))

		for edge in [e for e in self.graph.edges]:
			data.add_edge(edge[0], edge[1])

		return data

	def show_domain_admins(self):
		dst_sid = self.cn2sid('Domain Admins', True, self.domain_sid)
		return self.all_shortest_paths( dst_sid = dst_sid)
			
	def show_all_sources(self, src):
		src_sid = self.cn2sid(src, True, self.domain_sid)
		
		return self.all_shortest_paths(src_sid = src_sid)
	
	def get_node(self, nodeid = None):
		
		if nodeid is None:
			nodes = []
			for gid, props in list(self.graph.nodes(data=True)):
				nodes.append(GraphNode(gid, gid, properties = {}))
			return nodes

		if nodeid not in self.graph.nodes:
			return None
		gid, *t = self.graph.nodes[nodeid]
		return GraphNode(gid, gid, properties = {})


	def show_all_destinations(self, dst):
		dst_sid = self.cn2sid(dst, True, self.domain_sid)	
		return self.all_shortest_paths( dst_sid = dst_sid)
	
	def show_path(self, src, dst):
		src_sid = self.cn2sid(src, True, self.domain_sid)	
		dst_sid = self.cn2sid(dst, True, self.domain_sid)	

		return self.all_shortest_paths(src_sid = src_sid, dst_sid = dst_sid)
			
	def __add_path(self, network, path):
		"""
		Adds the path to the representational network
		Path is a list of sids (nodes), so we need to find the edges matching
		"""
		#print('PATH: %s' % repr(path))
		for d, sid in enumerate(path):
			#print(sid)
			network.add_node(sid, name = self.graph.nodes[sid].get('name', self.sid2cn(sid)), node_type = self.graph.nodes[sid].get('node_type'))
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
		
	#def plot(self, network):
	#	"""
	#	Creates and opens an HTML file representing the network
	#	
	#	network: pyvis network
	#	"""
	#	layout = Layout()
	#	layout.hierarchical.sortMethod = 'directed'
	#	layout.hierarchical.edgeMinimization = False
	#	layout.hierarchical.blockShifting = False
	#	layout.hierarchical.levelSeparation = 325
	#	layout.hierarchical.enabled = True
	#	layout.hierarchical.nodeSpacing = 325
	#	layout.hierarchical.treeSpacing = 250
	#	layout.hierarchical.direction = 'LR'
	#	network.options.layout = layout
	#	network.show_buttons(filter_=['layout'])
	#	network.show("test.html")
		
	def calc_acl_edges_sql(self, session, ad_id):
		#enumerating owners
		query = session.query(JackDawADDACL.owner_sid, JackDawADDACL.sid).filter(~JackDawADDACL.owner_sid.in_(["S-1-3-0", "S-1-5-18"])).filter(JackDawADDACL.ad_id == ad_id)
		for owner_sid, sid in query.all():
			self.add_edge(owner_sid, sid, label='Owner')
		
		#queriing generic access
		query = session.query(JackDawADDACL)\
						.filter(JackDawADDACL.ace_type == 'ACCESS_ALLOWED_ACE_TYPE')\
						.filter(~JackDawADDACL.ace_sid.in_(["S-1-3-0", "S-1-5-18"]))\
						.filter(JackDawADDACL.ad_id == ad_id)
		#print('ACCESS_ALLOWED_ACE_TYPE')
		for acl in query.all():
			if acl.ace_mask_generic_all == True:
				self.add_edge(acl.ace_sid, acl.sid, label='GenericALL')
			
			if acl.ace_mask_generic_write == True:
				self.add_edge(acl.ace_sid, acl.sid, label='GenericWrite')
				
			if acl.ace_mask_write_owner == True:
				self.add_edge(acl.ace_sid, acl.sid, label='WriteOwner')
				
			if acl.ace_mask_write_dacl == True:
				self.add_edge(acl.ace_sid, acl.sid, label='WriteDacl')
				
			if acl.object_type in ['user', 'domain'] and acl.ace_mask_control_access == True:
				self.add_edge(acl.ace_sid, acl.sid, label='ExtendedRightALL')
		
		#queriing only necessary fileds
		fields = ['ace_mask_generic_all', 'ace_mask_write_dacl', 'ace_mask_write_owner', 'ace_mask_generic_write', 'ace_objecttype', 'object_type', 'ace_mask_write_prop', 'ace_mask_control_access']
		#queriing object type access
		query = session.query(JackDawADDACL)\
						.options(load_only(*fields))\
						.filter(JackDawADDACL.ace_type == 'ACCESS_ALLOWED_OBJECT_ACE_TYPE')\
						.filter(JackDawADDACL.ad_id == ad_id)\
						.filter(~JackDawADDACL.ace_sid.in_(["S-1-3-0", "S-1-5-18"]))\
						.filter(~and_(JackDawADDACL.ace_hdr_flag_inherited == True, JackDawADDACL.ace_hdr_flag_inherit_only == True))\
						.filter(or_(JackDawADDACL.ace_hdr_flag_inherited == False,\
									JackDawADDACL.ace_hdr_flag_inherit_only == False,\
									and_(JackDawADDACL.ace_hdr_flag_inherited == True, JackDawADDACL.ace_hdr_flag_inherit_only == True, JackDawADDACL.ace_inheritedobjecttype == JackDawADDACL.object_type_guid)))
								

		#print('ACCESS_ALLOWED_OBJECT_ACE_TYPE')
		for acl in query.all():			
			if any([acl.ace_mask_generic_all, acl.ace_mask_write_dacl, acl.ace_mask_write_owner, acl.ace_mask_generic_write]):
				if acl.ace_objecttype is not None and not ace_applies(acl.ace_objecttype, acl.object_type):
					continue
				
				if acl.ace_mask_generic_all == True:
					self.add_edge(acl.ace_sid, acl.sid, label='GenericALL')
					continue
			
				if acl.ace_mask_generic_write == True:
					self.add_edge(acl.ace_sid, acl.sid, label='GenericWrite')
					
					if acl.object_type != 'domain':
						continue
					
				if acl.ace_mask_write_dacl == True:
					self.add_edge(acl.ace_sid, acl.sid, label='WriteDacl')
					
				if acl.ace_mask_write_owner == True:
					self.add_edge(acl.ace_sid, acl.sid, label='WriteOwner')
					
			if acl.ace_mask_write_prop == True:
				if acl.object_type in ['user','group'] and acl.ace_objecttype is None:
					self.add_edge(acl.ace_sid, acl.sid, label='GenericWrite')
					
				if acl.object_type == 'group' and acl.ace_objecttype == 'bf9679c0-0de6-11d0-a285-00aa003049e2':
					self.add_edge(acl.ace_sid, acl.sid, label='AddMember')
					
				
			
			if acl.ace_mask_control_access == True:
				if acl.object_type in ['user','group'] and acl.ace_objecttype is None:
					self.add_edge(acl.ace_sid, acl.sid, label='ExtendedAll')
				
				if acl.object_type == 'domain' and acl.ace_objecttype == '1131f6ad-9c07-11d1-f79f-00c04fc2dcd2':
					# 'Replicating Directory Changes All'
					self.add_edge(acl.ace_sid, acl.sid, label='GetChangesALL')
						
				if acl.object_type == 'domain' and acl.ace_objecttype == '1131f6aa-9c07-11d1-f79f-00c04fc2dcd2':
						# 'Replicating Directory Changes'
						self.add_edge(acl.ace_sid, acl.sid, label='GetChanges')
						
				if acl.object_type == 'user' and acl.ace_objecttype == '00299570-246d-11d0-a768-00aa006e0529':
						# 'Replicating Directory Changes'
						self.add_edge(acl.ace_sid, acl.sid, label='User-Force-Change-Password')
	
	def calc_acl_edges(self, adinfo):
		for acl in adinfo.objectacls:
			##SUPER-IMPORTANT!!!!
			##THE ACCESS RIGHTS CALCULATIONS ARE FLAWED (JUST LIKE IN BLOODHOUND)
			##CORRECT WAY WOULD BE TO TRAVERSE ALL ACES IN A GIVEN ACL IN THE ORDER OF "ACE-ODER" AND CHECK FOR DENY POLICIES AS WELL!!!
			##TODO: CALCULATE THE EFFECTIVE PERMISSIONS IN A CORRECT MANNER :)
			
			##TODO: The DB is designed that most of these calculations can (and should) be offloaded to the DB itself
			##      Currently it's in python bc I'm laze and Dirkjan already wrote the major part
			##      https://github.com/fox-it/BloodHound.py/blob/0d3897ba4cc00818c0fc3e01fa3a91fc42e799e2/bloodhound/enumeration/acls.py
			
			if acl.owner_sid not in self.ignoresids:
				self.add_edge(acl.owner_sid, acl.sid, label='Owner')
				
			if acl.ace_sid in self.ignoresids:
				continue
			
			if acl.ace_type in ['ACCESS_ALLOWED_ACE_TYPE','ACCESS_ALLOWED_OBJECT_ACE_TYPE']:
				if acl.ace_type == 'ACCESS_ALLOWED_ACE_TYPE':
					if acl.ace_mask_generic_all == True:
						self.add_edge(acl.ace_sid, acl.sid, label='GenericALL')
					
					if acl.ace_mask_generic_write == True:
						self.add_edge(acl.ace_sid, acl.sid, label='GenericWrite')
						
					if acl.ace_mask_write_owner == True:
						self.add_edge(acl.ace_sid, acl.sid, label='WriteOwner')
						
					if acl.ace_mask_write_dacl == True:
						self.add_edge(acl.ace_sid, acl.sid, label='WriteDacl')
						
					if acl.object_type in ['user', 'domain'] and acl.ace_mask_control_access == True:
						self.add_edge(acl.ace_sid, acl.sid, label='ExtendedRightALL')
				
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
							self.add_edge(acl.ace_sid, acl.sid, label='GenericALL')
							continue
				
						if acl.ace_mask_generic_write == True:
							self.add_edge(acl.ace_sid, acl.sid, label='GenericWrite')
							
							if acl.object_type != 'domain':
								continue
							
						if acl.ace_mask_write_dacl == True:
							self.add_edge(acl.ace_sid, acl.sid, label='WriteDacl')
							
						if acl.ace_mask_write_owner == True:
							self.add_edge(acl.ace_sid, acl.sid, label='WriteOwner')
							
					if acl.ace_mask_write_prop == True:
						if acl.object_type in ['user','group'] and acl.ace_objecttype is None:
							self.add_edge(acl.ace_sid, acl.sid, label='GenericWrite')
							
						if acl.object_type == 'group' and acl.ace_objecttype == 'bf9679c0-0de6-11d0-a285-00aa003049e2':
							self.add_edge(acl.ace_sid, acl.sid, label='AddMember')
							
						
				
					if acl.ace_mask_control_access == True:
						if acl.object_type in ['user','group'] and acl.ace_objecttype is None:
							self.add_edge(acl.ace_sid, acl.sid, label='ExtendedAll')
						
						if acl.object_type == 'domain' and acl.ace_objecttype == '1131f6ad-9c07-11d1-f79f-00c04fc2dcd2':
							# 'Replicating Directory Changes All'
							self.add_edge(acl.ace_sid, acl.sid, label='GetChangesALL')
								
						if acl.object_type == 'domain' and acl.ace_objecttype == '1131f6aa-9c07-11d1-f79f-00c04fc2dcd2':
								# 'Replicating Directory Changes'
								self.add_edge(acl.ace_sid, acl.sid, label='GetChanges')
								
						if acl.object_type == 'user' and acl.ace_objecttype == '00299570-246d-11d0-a768-00aa006e0529':
								# 'Replicating Directory Changes'
								self.add_edge(acl.ace_sid, acl.sid, label='User-Force-Change-Password')
		
	def construct(self, ad_id):
		"""
		Fills the network graph from database to memory
		"""
		self.ad_id = ad_id
		session = self.get_session()
		adinfo = session.query(JackDawADInfo).get(ad_id)
		
		self.domain_sid = str(adinfo.objectSid)
		
		node_lables = {}
		node_color_map = []
		
		distinct_filter = {}
		if self.show_group_memberships == True:
			#adding group nodes
			for group in adinfo.groups:
				#if group.sid in distinct_filter:
				#	continue
				#distinct_filter[group.sid] = 1
				self.add_sid_to_node(group.sid, 'group', name=group.name)
		
		#distinct_filter = {}
		if self.show_user_memberships == True:
			#adding user nodes
			for user in adinfo.users:
				self.add_sid_to_node(user.objectSid, 'user', name=user.sAMAccountName)
				
		distinct_filter = {}
		if self.show_machine_memberships == True:
			#adding user nodes
			for user in adinfo.computers:
				#if user.objectSid in distinct_filter:
				#	continue
				#distinct_filter[user.objectSid] = 1
				self.add_sid_to_node(user.objectSid, 'machine', name=user.sAMAccountName)
		
		
		if self.show_session_memberships == True:
			for res in session.query(JackDawADUser.objectSid, JackDawADMachine.objectSid).filter(NetSession.username == JackDawADUser.sAMAccountName).filter(NetSession.source == JackDawADMachine.sAMAccountName).distinct(NetSession.username):
				self.add_edge(res[0], res[1], label='hasSession')
				self.add_edge(res[1], res[0], label='hasSession')
		
		if self.show_localgroup_memberships == True:
			#TODO: maybe create edges based on local username similarities??
			for res in session.query(JackDawADUser.objectSid, JackDawADMachine.objectSid, LocalGroup.groupname).filter(LocalGroup.username == JackDawADUser.sAMAccountName).filter(LocalGroup.hostname == JackDawADMachine.sAMAccountName):
				label = None
				if res[3] == 'Remote Desktop Users':
					label = 'canRDP'
					weight = 1
					
				elif res[3] == 'Distributed COM Users':
					label = 'executeDCOM'
					weight = 1
					
				elif res[3] == 'Administrators':
					label = 'adminTo'
					weight = 1
					
				self.add_edge(res[0], res[1], label=label, weight = weight)
			
		if self.show_constrained_delegations == True:
			pass
			
			
		if self.show_unconstrained_delegations == True:
			pass
			
		if self.show_custom_relations == True:
			for res in adinfo.customrelations:
				self.add_edge(res.sid, res.target_sid)
			
		#print('adding membership edges')
		#adding membership edges
		for tokengroup in adinfo.group_lookups:
			self.add_sid_to_node(tokengroup.sid, 'unknown')
			self.add_sid_to_node(tokengroup.member_sid, 'unknown')
				
			if tokengroup.is_user == True and self.show_user_memberships == True:
				try:
					self.add_edge(tokengroup.sid, tokengroup.member_sid, label='member')
				except AssertionError as e:
					logger.exception()
			elif tokengroup.is_machine == True and self.show_machine_memberships == True:
				try:
					self.add_edge(tokengroup.sid, tokengroup.member_sid, label='member')
				except AssertionError as e:
					logger.exception()
			elif tokengroup.is_group == True and self.show_group_memberships == True:
				try:
					self.add_edge(tokengroup.sid, tokengroup.member_sid, label='member')
				except AssertionError as e:
					logger.exception()
		
		if self.show_acl == True:
			logger.info('Adding ACL edges')
			#adding ACL edges
			self.calc_acl_edges(adinfo)
			#self.calc_acl_edges_sql(session, ad_id)
		else:
			logger.info('Not adding ACL edges')
		
						
				
					