import os
from gzip import GzipFile
import pathlib
import multiprocessing as mp
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
from jackdaw.wintypes.well_known_sids import get_name_or_sid, get_sid_for_name
import tempfile
from tqdm import tqdm
from sqlalchemy import func
import graph_tool
from graph_tool.topology import all_shortest_paths, shortest_path, shortest_distance


class JackDawDomainGraphGrapthTools:
	graph_file_name = 'graphtools.csv'
	def __init__(self, dbsession, graph_id):
		self.dbsession = dbsession
		self.graph_id = int(graph_id)
		self.constructs = {}
		self.graph = None
		self.domain_sid = None
		self.domain_id = None
		self.lookup = {}

	def __resolv_edge_types(self, src_id, dst_id):
		t = []
		for res in self.dbsession.query(Edge.label).distinct(Edge.label).filter_by(graph_id = self.graph_id).filter(Edge.ad_id == self.domain_id).filter(Edge.src == src_id).filter(Edge.dst == dst_id).all():
			t.append(res)
		return t

	def __resolve_sid_to_id(self, sid):
		for res in self.dbsession.query(EdgeLookup.id).filter_by(ad_id = self.domain_id).filter(EdgeLookup.oid == sid).first():
			return res
		return None

	def __nodename_to_sid(self, node_name):
		node_name = int(node_name)
		if node_name in self.lookup:
			return self.lookup[node_name]
		t = self.dbsession.query(EdgeLookup).get(node_name) #node_name is the ID of the edgelookup
		self.lookup[node_name] = (t.oid, t.otype)
		return t.oid, t.otype		

	def save(self):
		pass

	def setup(self):
		gi = self.dbsession.query(GraphInfo).get(self.graph_id)
		domaininfo = self.dbsession.query(ADInfo).get(gi.ad_id)
		self.domain_sid = domaininfo.objectSid
		self.domain_id = gi.ad_id
	
	@staticmethod
	def create(dbsession, ad_id, graph_id, graph_dir):
		graph_file = graph_dir.joinpath(JackDawDomainGraphGrapthTools.graph_file_name)

		logger.debug('Creating a new graph file: %s' % graph_file)

		## remove this
		fi = dbsession.query(EdgeLookup.id).filter_by(ad_id = ad_id).filter(EdgeLookup.oid == 'S-1-5-32-545').first()
		fi = fi[0]
		##

		t2 = dbsession.query(func.count(Edge.id)).filter_by(graph_id = graph_id).filter(EdgeLookup.id == Edge.src).filter(EdgeLookup.oid != None).scalar()
		q = dbsession.query(Edge).filter_by(graph_id = graph_id).filter(EdgeLookup.id == Edge.src).filter(EdgeLookup.oid != None)

		with open(graph_file, 'w', newline = '') as f:
			for edge in tqdm(windowed_query(q,Edge.id, 10000), desc = 'edge', total = t2):
				r = '%s,%s\r\n' % (edge.src, edge.dst)
				f.write(r)
		logger.debug('Graph created!')

	@staticmethod
	def load(dbsession, graph_id, graph_cache_dir):
		logger.info('Loading Graphcache file to memory')
		graph_file = graph_cache_dir.joinpath(JackDawDomainGraphGrapthTools.graph_file_name)
		g = JackDawDomainGraphGrapthTools(dbsession, graph_id)
		g.graph = graph_tool.load_graph_from_csv(str(graph_file), directed=True, string_vals=False, hashed=False)
		g.setup()
		logger.debug('Graph loaded to memory')
		logger.info('Loaded Graphcache file to memory OK')
		return g

	def all_shortest_paths(self, src_sid = None, dst_sid = None):
		nv = GraphData()
		if src_sid is None and dst_sid is None:
			raise Exception('src_sid or dst_sid must be set')
		elif src_sid is None and dst_sid is not None:
			dst = self.__resolve_sid_to_id(dst_sid)
			if dst is None:
				raise Exception('SID not found!')
			
			total = self.dbsession.query(func.count(EdgeLookup.id)).filter_by(ad_id = self.domain_id).filter(EdgeLookup.oid != self.domain_sid + '-513').scalar()
			q = self.dbsession.query(EdgeLookup.id).filter_by(ad_id = self.domain_id).filter(EdgeLookup.oid != self.domain_sid + '-513')
			for nodeid in tqdm(windowed_query(q, EdgeLookup.id, 1000), desc = 'running', total = total):
				for path in all_shortest_paths(self.graph, nodeid[0], dst):
					print(path)
					self.__result_path_add(nv, path)

		elif src_sid is not None and dst_sid is not None:
			print(1)
			print(src_sid)
			print(dst_sid)
			src = self.__resolve_sid_to_id(src_sid)
			if src is None:
				raise Exception('SID not found!')
			
			dst = self.__resolve_sid_to_id(dst_sid)
			if dst is None:
				raise Exception('SID not found!')
			
			print(src)
			print(dst)

			for path in all_shortest_paths(self.graph, src, dst):
				print(path)
				self.__result_path_add(nv, path)

		return nv

	def shortest_paths(self, src_sid = None, dst_sid = None):
		nv = GraphData()
		if src_sid is None and dst_sid is None:
			raise Exception('src_sid or dst_sid must be set')
		elif src_sid is None and dst_sid is not None:
			dst = self.__resolve_sid_to_id(dst_sid)
			if dst is None:
				raise Exception('SID not found!')


			total = self.dbsession.query(func.count(EdgeLookup.id)).filter_by(ad_id = self.domain_id).filter(EdgeLookup.oid != self.domain_sid + '-513').scalar()
			q = self.dbsession.query(EdgeLookup.id).filter_by(ad_id = self.domain_id).filter(EdgeLookup.oid != self.domain_sid + '-513')
			for nodeid in tqdm(windowed_query(q, EdgeLookup.id, 1000), desc = 'running', total = total):
				for i, res in enumerate(shortest_path(self.graph, nodeid, dst)):
					if res == []:
						continue
					if i % 2 == 0:
						self.__result_path_add(nv, res)


		elif src_sid is not None and dst_sid is not None:
			dst = self.__resolve_sid_to_id(dst_sid)
			if dst is None:
				raise Exception('SID not found!')

			src = self.__resolve_sid_to_id(src_sid)
			if src is None:
				raise Exception('SID not found!')
			
			for i, res in enumerate(shortest_path(self.graph, src, dst)):
				if res == []:
					continue
				if i % 2 == 0:
					self.__result_path_add(nv, res)
		
		else:
			raise Exception('Not implemented!')

		return nv
	
	def __result_path_add(self, network, path):
		if path == []:
			return
		path = [i for i in path]
		delete_this = []
		for d, node_id in enumerate(path):
			sid, otype = self.__nodename_to_sid(node_id)
			delete_this.append('%s(%s) -> ' % (sid, otype))
			network.add_node(
				sid, 
				name = self.__sid2cn(sid, otype), 
				node_type = otype,
				domainid = self.domain_id
			)
			network.nodes[sid].set_distance(len(path)-d-1)

		print(''.join(delete_this))
		for i in range(len(path) - 1):
			self.__result_edge_add(network, int(path[i]), int(path[i+1]))

	def __result_edge_add(self, network, src_id, dst_id):
		for label in self.__resolv_edge_types(src_id, dst_id):
				try:
					src = self.__nodename_to_sid(src_id)
					dst = self.__nodename_to_sid(dst_id)
					network.add_edge(src[0],dst[0], label=label[0])
					print('%s -> %s [%s]' % (src, dst, label))
				except Exception as e:
					import traceback
					traceback.print_exc()
					print(e)

	def __sid2cn(self, sid, otype):
		if otype == 'user':
			tsid = self.dbsession.query(ADUser.cn).filter(ADUser.objectSid == sid).first()
			if tsid is not None:
				return tsid[0]
		
		elif otype == 'group':
			tsid = self.dbsession.query(Group.cn).filter(Group.objectSid == sid).first()
			if tsid is not None:
				return tsid[0]

		elif otype == 'machine':
			tsid = self.dbsession.query(Machine.cn).filter(Machine.objectSid == sid).first()
			if tsid is not None:
				return tsid[0]

		elif otype == 'trust':
			tsid = self.dbsession.query(ADTrust.cn).filter(ADTrust.securityIdentifier == sid).first()
			if tsid is not None:
				return tsid[0]
		
		else:
			return None

	def has_path(self, src_sid, dst_sid):
		# https://stackoverflow.com/questions/52414426/has-path-equivalent-in-graph-tool
		dst = self.__resolve_sid_to_id(dst_sid)
		if dst is None:
			raise Exception('SID not found!')

		src = self.__resolve_sid_to_id(src_sid)
		if src is None:
			raise Exception('SID not found!')
		
		return shortest_distance(self.graph, src, dst) < self.graph.num_vertices()

	def get_domainsids(self):
		pass

	def get_nodes(self):
		pass

	def get_distances_from_node(self):
		pass
