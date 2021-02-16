

import math

class NodeNotFoundException(Exception):
	pass

class GraphNode:
	def __init__(self, gid, name, domainid, gtype = None, properties = {}, owned = False, highvalue = False):
		self.name = name
		self.id = gid
		self.domainid = domainid
		self.type = gtype
		self.properties = properties
		self.mindistance = math.inf
		self.owned = owned
		self.highvalue = highvalue

	def set_distance(self, d):
		self.mindistance = min(self.mindistance, d)

	def serialize_mindistance(self):
		if self.mindistance == math.inf:
			return 999999
		return self.mindistance

	def to_dict(self, format = None):
		if format is None:
			return {
				'id' : self.id,
				'name' : self.name,
				'domainid' : self.domainid,
				'properties' : self.properties,
				'md' : self.serialize_mindistance(),
				'owned' : self.owned,
				'highvalue' : self.highvalue,
			}

		elif format == 'd3':
			return {
				'id' : self.id,
				'name' : self.name,
				'domainid' : self.domainid,
				'type' : self.type,
				'md' : self.serialize_mindistance(),
				'owned' : self.owned,
				'highvalue' : self.highvalue,
			}
		
		elif format == 'vis':
			return {
				'id' : self.id,
				'label' : self.name,
				'type' : self.type,
				'domainid' : self.domainid,
				'md' : self.serialize_mindistance(),
				'owned' : self.owned,
				'highvalue' : self.highvalue,
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
		self.edges = {}

	def node_present(self, node):
		if node in self.nodes:
			return True
		return False

	def add_node(self, gid, name, domainid, node_type, properties = {}, owned = False, highvalue = False):
		self.nodes[gid] = GraphNode(gid, name, domainid, node_type, properties, owned = owned, highvalue = highvalue)
	
	def add_edge(self, src, dst, label = '', weight = 1, properties = {}):
		if src not in self.nodes:
			raise NodeNotFoundException('Node (src) with id %s is not present' % src)
		if dst not in self.nodes:
			raise NodeNotFoundException('Node (dst) with id %s is not present' % dst)
		
		key = str(src) + str(dst) + str(label)

		self.edges[key] = GraphEdge(src, dst, label, weight, properties)

	def __add__(self, o):
		if not isinstance(o, GraphData):
			raise Exception('Cannot add GraphData and %s' % type(o))
		
		self.nodes.update(o.nodes)
		self.edges.update(o.edges)
		return self

	def to_dict(self, format = None):
		if format is None:
			return {
				'nodes' : [self.nodes[x].to_dict() for x in self.nodes],
				'edges' : [self.edges[x].to_dict() for x in self.edges]
			}
		elif format == 'd3':
			return {
				'nodes' : [self.nodes[x].to_dict(format = format) for x in self.nodes],
				'links' : [self.edges[x].to_dict(format = format) for x in self.edges]
			}
		elif format == 'vis':
			return {
				'nodes' : [self.nodes[x].to_dict(format = format) for x in self.nodes],
				'edges' : [self.edges[x].to_dict(format = format) for x in self.edges]
			}