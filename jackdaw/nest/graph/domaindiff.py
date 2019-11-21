
from jackdaw.nest.graph.domain import DomainGraph

class DomainDiff:
	def __init__(self, db_conn = None, dbsession = None):
		self.db_conn = db_conn
		self.dbsession = dbsession
		self.old_graph = None
		self.new_graph = None

		self.users_added = {}
		self.users_removed = {}

		self.machines_added = {}
		self.machines_removed = {}

		self.groups_added = {}
		self.groups_removed = {}

		self.ous_added = {}
		self.ous_removed = {}

	def diff_nodes(self):
		for sid, attrs in self.new_graph.graph.nodes(data=True):
			print(sid)
			if not self.old_graph.graph.has_node(sid):
				print(attrs)
				if attrs.get('node_type') == 'user':
					self.users_added[sid] = {
						'name' : attrs['name'],
						'adid' : attrs['construct'].ad_id,
					}
				elif attrs.get('node_type') == 'machine':
					self.machines_added[sid] = {
						'name' : attrs['name'],
						'adid' : attrs['construct'].ad_id,
					}
				elif attrs.get('node_type') == 'group':
					self.groups_added[sid] = {
						'name' : attrs['name'],
						'adid' : attrs['construct'].ad_id,
					}
	
		for sid, attrs in self.old_graph.graph.nodes(data=True):
			if not self.new_graph.graph.has_node(sid):
				if attrs.get('node_type') == 'user':
					self.users_removed[sid] = {
						'name' : attrs['name'],
						'adid' : attrs['construct'].ad_id,
					}
				elif attrs.get('node_type') == 'machine':
					self.machines_removed[sid] = {
						'name' : attrs['name'],
						'adid' : attrs['construct'].ad_id,
					}
				elif attrs.get('node_type') == 'group':
					self.groups_removed[sid] = {
						'name' : attrs['name'],
						'adid' : attrs['construct'].ad_id,
					}

		node_diff = {
			'users_added' : self.users_added,
			'users_removed' : self.users_removed,
			'machines_added' : self.machines_added,
			'machines_removed' : self.machines_removed,
			'groups_added' : self.groups_added,
			'groups_removed' : self.groups_removed,
			'ous_added' : self.ous_added,
			'ous_removed' : self.ous_removed,
		}

		return node_diff

	def diff_edges(self):
		pass

	def diff_path(self, srcsid = None, dstsid = None):
		if srcsid is None and dstsid is None:
			raise Exception('Either src or dst must be provided, or both!')
		if srcsid is not None:
			if not self.old_graph.graph.has_node(srcsid):
				raise Exception('srcsid not found in old version!')
			if not self.new_graph.graph.has_node(srcsid):
				raise Exception('srcsid not found in new version!')
		if dstsid is not None:
			if not self.old_graph.graph.has_node(dstsid):
				raise Exception('dstsid not found in old version!')
			if not self.new_graph.graph.has_node(dstsid):
				raise Exception('dstsid not found in new version!')

		path_old = self.old_graph.all_shortest_paths(srcsid, dstsid)
		path_new = self.new_graph.all_shortest_paths(srcsid, dstsid)


	def diff_path_da(self):
		return {}

	def diff_path_distance(self, sid):
		if not self.old_graph.graph.has_node(sid):
			raise Exception('sid not found in old version!')
		if not self.new_graph.graph.has_node(sid):
			raise Exception('sid not found in new version!')
		old_dist = self.old_graph.distances_from_node(sid)
		new_dist = self.new_graph.distances_from_node(sid)

		merged = {}
		for dist in old_dist:
			if dist in new_dist:
				merged[dist] = new_dist[dist] - old_dist[dist]
			else:
				merged[dist] = 0 - old_dist[dist]
		for dist in new_dist:
			if dist not in new_dist:
				merged[dist] = new_dist[dist]

		return merged
				

	def construct(self, construct_old, construct_new):
		construct_old.diff_name = 'old'
		self.old_graph = DomainGraph(dbsession = self.dbsession)
		self.old_graph.construct(construct_old)

		construct_new.diff_name = 'new'
		self.new_graph = DomainGraph(dbsession = self.dbsession)
		self.new_graph.construct(construct_new)
