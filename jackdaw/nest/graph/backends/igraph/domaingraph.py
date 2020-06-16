import os
from gzip import GzipFile
import pathlib
import multiprocessing as mp
import networkx as nx
from bidict import bidict
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
from jackdaw.nest.graph.construct import GraphConstruct
from jackdaw.wintypes.well_known_sids import get_name_or_sid, get_sid_for_name
import igraph
import tempfile
from tqdm import tqdm
from sqlalchemy import func


class JackDawDomainGraphIGraph:
	def __init__(self, dbsession, graph_id):
		self.dbsession = dbsession
		self.graph_id = graph_id
		self.constructs = {}
		self.graph = igraph.Graph(directed = True)
		self.domain_sid = None
		self.domain_id = None

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
		t = self.dbsession.query(EdgeLookup).get(node_name) #node_name is the ID of the edgelookup
		return t.oid, t.otype


	def __nodeid_to_sid(self, node_id):
		return self.__nodename_to_sid(self.graph.vs[node_id]['name'])
		

	def save(self):
		pass

	def load(self):
		graphinfo = self.dbsession.query(GraphInfo).get(self.graph_id)
		domaininfo = self.dbsession.query(ADInfo).get(graphinfo.ad_id)
		self.domain_sid = domaininfo.objectSid
		self.domain_id = domaininfo.id

		fname = 'tempfile.bla'
		t2 = self.dbsession.query(func.count(Edge.id)).filter_by(graph_id = self.graph_id).scalar()
		q = self.dbsession.query(Edge).filter_by(graph_id = self.graph_id)

		with open(fname, 'w', newline = '') as f:
			for edge in tqdm(windowed_query(q,Edge.id, 10000), desc = 'edge', total = t2):
				r = '%s %s %s\r\n' % (edge.src, edge.dst, edge.label)
				f.write(r)

		self.graph = igraph.Graph.Read_Ncol(fname, directed=True)

		os.unlink(fname)
		print('Added!')

	def all_shortest_paths(self, src_sid = None, dst_sid = None):
		nv = GraphData()
		if src_sid is None and dst_sid is None:
			raise Exception('src_sid or dst_sid must be set')
		elif src_sid is None and dst_sid is not None:
			dst = self.__resolve_sid_to_id(dst_sid)
			if dst is None:
				raise Exception('SID not found!')
				
			# IN will give reverse order!!!!
			for path in self.graph.get_shortest_paths(str(dst), mode= igraph._igraph.IN):
				self.__result_path_add(nv, path)

				
		elif src_sid is not None and dst_sid is None:
			src = self.__resolve_sid_to_id(dst_sid)
			if src is None:
				raise Exception('SID not found!')
			
			for path in self.graph.get_all_shortest_paths(str(src), mode= self.graph.OUT):
				self.__result_path_add(nv, path)

		elif src_sid is not None and dst_sid is not None:
			src = self.__resolve_sid_to_id(dst_sid)
			if src is None:
				raise Exception('SID not found!')
			
			dst = self.__resolve_sid_to_id(dst_sid)
			if dst is None:
				raise Exception('SID not found!')
			
			for path in self.graph.get_all_shortest_paths(str(src), to = str(dst), mode= self.graph.OUT):
				self.__result_path_add(nv, path)

		return nv
	
	def __result_path_add(self, network, path):
		if path == []:
			return
		
		for d, node_id in enumerate(path):
			sid, otype = self.__nodeid_to_sid(node_id)
			network.add_node(
				sid, 
				name = self.__sid2cn(sid, otype), 
				node_type = otype,
				domainid = self.domain_id
			)
			network.nodes[sid].set_distance(d)

		for i in range(len(path) - 1):
			for label in self.__resolv_edge_types(self.graph.vs[path[i]]['name'], self.graph.vs[path[i+1]]['name']):
				try:
					src = self.__nodeid_to_sid(path[i])
					dst = self.__nodeid_to_sid(path[i+1])
					network.add_edge(src[0],dst[0], label=label)
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

	def get_domainsids(self):
		pass

	def get_nodes(self):
		pass

	def get_distances_from_node(self):
		pass
