import copy

from jackdaw import logger
from jackdaw.dbmodel.adtrust import ADTrust
from jackdaw.dbmodel.adcomp import Machine
from jackdaw.dbmodel.aduser import ADUser
from jackdaw.dbmodel.adgroup import Group
from jackdaw.dbmodel.adinfo import ADInfo
from jackdaw.dbmodel.graphinfo import GraphInfo
from jackdaw.dbmodel.edge import Edge
from jackdaw.dbmodel.edgelookup import EdgeLookup
from jackdaw.dbmodel import windowed_query
from jackdaw.nest.graph.graphdata import GraphData, GraphNode
from jackdaw.dbmodel.graphinfo import GraphInfo, GraphInfoAD
from jackdaw.dbmodel.adobjprops import ADObjProps


class JackDawDomainGraph:
	def __init__(self, dbsession, graph_id, graph_dir, use_cache = False):

		self.dbsession = dbsession
		self.graph_id = int(graph_id)
		self.use_cache = False # TODO
		self.graph_dir = graph_dir
		self.graph = None
		self.adids = []

		self.name_sid_lookup = {}
		self.props_lookup = {}
		self.sid_adid_lookup = {}
		self.sid_name_lookup = {}
		self.label_lookup = {}

	def result_path_add(self, network, path, exclude = [], pathonly = False):
		if pathonly is False:
			if len(exclude) > 0:
				if self.check_path_exclude(path, exclude) is False:
					# path contains edges which are excluded
					return

			for i in range(len(path) - 1):
				self.result_edge_add(network, int(path[i]), int(path[i+1]), path, exclude = exclude)
		else:
			res = [[]]
			nolabel = False
			for i in range(len(path) - 1):
				for r in res:
					r.append(self.nodename_to_sid(int(path[i])))
				labels = []
				for label in self.resolv_edge_types(int(path[i]), int(path[i+1])):
					if label not in exclude:
						labels.append(label)
				if len(labels) == 0:
					nolabel = True
					break
				if len(labels) == 1:
					for r in res:
						r.append(labels[0])
				else:
					temp = []
					for label in labels:
						for r in res:
							x = copy.deepcopy(r)
							x.append(label)
							temp.append(x)

					res = temp

				#res.append(labels)
			if nolabel is True:
				return
			for r in res:
				r.append(self.nodename_to_sid(int(path[-1])))
			
			
			network += res
	
	def add_nodes_from_path(self, network, path):
		if path == []:
			return
		path = [i for i in path]
		#delete_this = []
		for d, node_id in enumerate(path):
			sid, otype = self.nodename_to_sid(node_id)
		
			if sid not in self.sid_adid_lookup:
				res = self.dbsession.query(EdgeLookup).filter_by(oid = sid).first()
				self.sid_adid_lookup[sid] = res.ad_id
			
			domain_id = self.sid_adid_lookup[sid]
			owned, highvalue = self.get_props(sid)
			#delete_this.append('%s(%s) -> ' % (sid, otype))
			network.add_node(
				sid, 
				name = self.sid2cn(sid, otype), 
				node_type = otype,
				domainid = domain_id,
				owned = owned,
				highvalue = highvalue
			)
			network.nodes[sid].set_distance(len(path)-d-1)

	def add_node(self, network, nodeid):
		sid, otype = self.nodename_to_sid(nodeid)
		if network.node_present(sid) is True:
			return sid

		if sid not in self.sid_adid_lookup:
			res = self.dbsession.query(EdgeLookup).filter_by(oid = sid).first()
			self.sid_adid_lookup[sid] = res.ad_id

		domain_id = self.sid_adid_lookup[sid]
		owned, highvalue = self.get_props(sid)
		network.add_node(
			sid, 
			name = self.sid2cn(sid, otype), 
			node_type = otype,
			domainid = domain_id,
			owned = owned,
			highvalue = highvalue
		)
		return sid

	def check_path_exclude(self, path, exclude):
		if len(exclude) == 0:
			return True
		for i in range(len(path) - 1):
			for label in self.resolv_edge_types(int(path[i]), int(path[i+1])):
				if label in exclude:
					return False
		return True

	def result_edge_add(self, network, src_id, dst_id, path, exclude = []):
		labels = []
		for label in self.resolv_edge_types(src_id, dst_id):
			if label not in exclude:
				labels.append(label)
			
		if len(labels) != 0:
			src_sid = self.add_node(network, src_id)
			dst_sid = self.add_node(network, dst_id)
			for label in labels:
				network.add_edge(src_sid, dst_sid, label=label)
			
			return True
		
		return False		
	
	def nodename_to_sid(self, node_name):
		node_name = int(node_name)
		if node_name in self.name_sid_lookup:
			return self.name_sid_lookup[node_name]
		t = self.dbsession.query(EdgeLookup).get(node_name) #node_name is the ID of the edgelookup
		self.name_sid_lookup[node_name] = (t.oid, t.otype)
		return t.oid, t.otype

	def get_props(self, oid):
		if oid not in self.props_lookup:
			qry = self.dbsession.query(ADObjProps).filter_by(oid=oid).filter(ADObjProps.graph_id==self.graph_id)
			owned_res = qry.filter(ADObjProps.prop == 'OWNED').first()
			if owned_res is not None:
				owned_res = True
			highvalue_res = qry.filter(ADObjProps.prop == 'HVT').first()
			if highvalue_res is not None:
				highvalue_res = True
			self.props_lookup[oid] = (owned_res, highvalue_res)
		return self.props_lookup[oid]

	
	def resolv_edge_types(self, src_id, dst_id):
		key = '%s_%s' % (str(src_id), str(dst_id))
		if key not in self.label_lookup:
			self.label_lookup[key] = []
			for domain_id in self.adids:
				for res in self.dbsession.query(Edge.label).distinct(Edge.label).filter_by(graph_id = self.graph_id).filter(Edge.ad_id == domain_id).filter(Edge.src == src_id).filter(Edge.dst == dst_id).all():
					self.label_lookup[key].append(res[0])
		
		for label in self.label_lookup[key]:
			yield label

	def resolve_sid_to_id(self, sid):
		#print('resolve_sid_to_id sid %s' % sid)
		for domain_id in self.adids:
			for res in self.dbsession.query(EdgeLookup.id).filter_by(ad_id = domain_id).filter(EdgeLookup.oid == sid).first():
				#print('resolve_sid_to_id res %s' % res)
				return res
		return None


	def sid2cn(self, sid, otype):
		tsid = None
		if sid not in self.sid_name_lookup:
			if otype == 'user':
				tsid = self.dbsession.query(ADUser.sAMAccountName).filter(ADUser.objectSid == sid).first()
				if tsid is not None:
					self.sid_name_lookup[sid] = tsid[0]
			
			elif otype == 'group':
				tsid = self.dbsession.query(Group.sAMAccountName).filter(Group.objectSid == sid).first()
				if tsid is not None:
					self.sid_name_lookup[sid] = tsid[0]

			elif otype == 'machine':
				tsid = self.dbsession.query(Machine.sAMAccountName).filter(Machine.objectSid == sid).first()
				if tsid is not None:
					self.sid_name_lookup[sid] = tsid[0]

			elif otype == 'trust':
				tsid = self.dbsession.query(ADTrust.dn).filter(ADTrust.securityIdentifier == sid).first()
				if tsid is not None:
					self.sid_name_lookup[sid] = tsid[0]
			
			elif otype == 'domain':
				tsid = self.dbsession.query(ADInfo.distinguishedName).filter(ADInfo.objectSid == sid).first()
				if tsid is not None:
					self.sid_name_lookup[sid] = tsid[0]
		
			else:
				print('sid2cn unknown otype "%s" for sid %s' % (otype, sid))
				self.sid_name_lookup[sid] = None
		
		if sid not in self.sid_name_lookup:
			print('sid2cn could not find %s with sid "%s" in the database.' % (otype, sid))
			self.sid_name_lookup[sid] = None

		return self.sid_name_lookup[sid]

	def get_edges_onelevel(self, target_sid, edge_type, direction = 'IN'):
		try:
			target_id = self.resolve_sid_to_id(target_sid)

			direction = direction.upper()
			if direction not in ['IN', 'OUT']:
				raise Exception('direction not recognized: %s' % direction)

			if direction == 'IN':
				for res in self.dbsession.query(Edge.src).filter_by(dst = target_id).filter(Edge.graph_id == self.graph_id).filter(Edge.label == edge_type).all():
					yield self.nodename_to_sid(int(res[0]))
			else: #direction == 'OUT':
				for res in self.dbsession.query(Edge.dst).filter_by(src = target_id).filter(Edge.graph_id == self.graph_id).filter(Edge.label == edge_type).all():
					yield self.nodename_to_sid(int(res[0]))
			
		except Exception as e:
			import traceback
			traceback.print_exc()
			print(e)
			raise e
	
	def get_members(self, group_sid, maxhops = 1):
		try:
			network = GraphData()
			
			group_id = self.resolve_sid_to_id(group_sid)
			self.add_node(network, group_id)
			prev_groups = [group_sid]
			for distance in range(maxhops):
				next_groups = []
				for group_sid in prev_groups:
					for sid, otype in self.get_edges_onelevel(group_sid, 'member', 'in'):
						if otype == 'group':
							next_groups.append(sid)
						if network.node_present(sid) is False:
							rid = self.resolve_sid_to_id(sid)
							self.add_node(network, rid)
						
						network.nodes[sid].set_distance(distance)
						network.add_edge(group_sid, sid, label='member')

				prev_groups = next_groups
			
			return network
		except Exception as e:
			import traceback
			traceback.print_exc()
			print(e)
			raise e

	def get_dcsync(self):
		try:
			network = GraphData()
			forest_sids = []
			groups = []
			for adid in self.adids:
				adinfo = self.dbsession.query(ADInfo).get(adid)
				forest_sids.append(adinfo.objectSid)

			for forest_sid in forest_sids:
				self.add_node(network, self.resolve_sid_to_id(forest_sid))
				for sid, otype in self.get_edges_onelevel(forest_sid, 'GetChanges', 'in'):
					if otype == 'group':
						groups.append(sid)
					if network.node_present(sid) is False:
						rid = self.resolve_sid_to_id(sid)
						self.add_node(network, rid)
					
					network.add_edge(forest_sid, sid, label='GetChanges')
				
				for sid, otype in self.get_edges_onelevel(forest_sid, 'GetChangesAll', 'in'):
					if otype == 'group':
						groups.append(sid)
					if network.node_present(sid) is False:
						rid = self.resolve_sid_to_id(sid)
						self.add_node(network, rid)
					
					network.add_edge(forest_sid, sid, label='GetChangesAll')
			
			for group_sid in groups:
				network += self.get_members(group_sid, 1)
			
			return network
		except Exception as e:
			import traceback
			traceback.print_exc()
			print(e)
			raise e
