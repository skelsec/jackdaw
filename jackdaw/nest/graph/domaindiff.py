


class DomainDiff:
	def __init__(self):
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
					self.users_added[sid] = 1
				elif attrs.get('node_type') == 'machine':
					self.machines_added[sid] = 1
				elif attrs.get('node_type') == 'group':
					self.groups_added[sid] = 1
	
		for sid, attrs in self.old_graph.graph.nodes(data=True):
			if not self.new_graph.graph.has_node(sid):
				print(attrs)
				if attrs.get('node_type') == 'user':
					self.users_removed[sid] = 1
				elif attrs.get('node_type') == 'machine':
					self.machines_removed[sid] = 1
				elif attrs.get('node_type') == 'group':
					self.groups_removed[sid] = 1

	def diff_edges(self):
		pass

	def diff_path(self, src = None, dst = None):
		if not self.old_graph.graph.has_node(sid):
			raise Exception('Node not found in old version!')
		if not self.new_graph.graph.has_node(sid):
			raise Exception('Node not found in new version!')

		path_old = self.old_graph.all_shortest_paths(src, dst)
		path_new = self.new_graph.all_shortest_paths(src, dst)


	def diff_path_distance(self, sid):
		old_dist = self.old_graph.distances_from_node(sid)
		new_dist = self.new_graph.distances_from_node(sid)

	def construct(self, construct_old, construct_new):
		self.old_graph = DomainGraph(dbsession = db.session)
		self.old_graph.construct(construct_old)

		self.old_graph = DomainGraph(dbsession = db.session)
		self.old_graph.construct(construct_old)
