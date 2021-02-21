import os
import pathlib
import platform

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
from jackdaw.dbmodel.graphinfo import GraphInfo, GraphInfoAD
from jackdaw.dbmodel.adobjprops import ADObjProps

import igraph
from tqdm import tqdm
from sqlalchemy import func
import traceback



class JackDawDomainGraphIGraph:
	graph_file_name = 'networkx.csv' #it is the same format
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

	def __resolv_edge_types(self, src_id, dst_id):
		t = []
		for res in self.dbsession.query(Edge.label).distinct(Edge.label).filter_by(graph_id = self.graph_id).filter(Edge.ad_id == self.domain_id).filter(Edge.src == src_id).filter(Edge.dst == dst_id).all():
			t.append(res)
		return t

	def __nodename_to_sid(self, node_name):
		t = self.dbsession.query(EdgeLookup).get(node_name) #node_name is the ID of the edgelookup
		return t.oid, t.otype


	def __nodeid_to_sid(self, node_id):
		return self.__nodename_to_sid(self.graph.vs[node_id]['name'])
		

	def save(self):
		pass

	def setup(self):
		gi = self.dbsession.query(GraphInfo).get(self.graph_id)
		for graphad in self.dbsession.query(GraphInfoAD).filter_by(graph_id = gi.id).all():
			self.adids.append(graphad.ad_id)
	
	@staticmethod
	def create(dbsession, graph_id, graph_dir, sqlite_file = None):
		logger.info('Create called!')
		graph_id = int(graph_id)
		graph_file = graph_dir.joinpath(JackDawDomainGraphIGraph.graph_file_name)

		logger.debug('Creating a new graph file: %s' % graph_file)
		
		adids = dbsession.query(GraphInfoAD.ad_id).filter_by(graph_id = graph_id).all()
		if adids is None:
			raise Exception('No ADIDS were found for graph %s' % graph_id)
		
		using_sqlite_tool = False
		if sqlite_file is not None:
			logger.info('Trying sqlite3 dumping method...')
			# This is a hack.
			# Problem: using sqlalchemy to dump a large table (to get the graph data file) is extremely resource intensive 
			# Solution: if sqlite is used as the database backend we can use the sqlite3 cmdline utility to do the dumping much faster
			# 

			sf = sqlite_file
			gf = graph_file
			if platform.system() == 'Windows':
				sf = sf.replace('\\', '\\\\')
				gf = gf.replace('\\', '\\\\')
			qry_str = '.open %s\r\n.mode csv\r\n.output %s\r\n.separator " "\r\nSELECT src,dst FROM adedges, adedgelookup WHERE adedges.graph_id = %s AND adedgelookup.id = adedges.src AND adedgelookup.oid IS NOT NULL;\r\n.exit' % (sf, graph_file, graph_id)
			with open('buildnode.sql', 'w', newline='') as f:
				f.write(qry_str)
			
			import subprocess
			import shlex
			
			cmd = 'cat buildnode.sql | sqlite3'
			if platform.system() == 'Windows':
				cmd = 'type buildnode.sql | sqlite3'
			process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
			_, stderr = process.communicate()
			process.wait()
			
			if process.returncode == 0:
				using_sqlite_tool = True
				logger.info('sqlite3 dumping method OK!')
			else:
				logger.warning('Failed to use the sqlite3 tool to speed up graph datafile generation. Reason: %s' % stderr)
				

		if using_sqlite_tool is False:
		
			for ad_id in adids:
				ad_id = ad_id[0]
				t2 = dbsession.query(func.count(Edge.id)).filter_by(graph_id = graph_id).filter(EdgeLookup.id == Edge.src).filter(EdgeLookup.oid != None).scalar()
				q = dbsession.query(Edge).filter_by(graph_id = graph_id).filter(EdgeLookup.id == Edge.src).filter(EdgeLookup.oid != None)

				with open(graph_file, 'w', newline = '') as f:
					for edge in tqdm(windowed_query(q,Edge.id, 10000), desc = 'edge', total = t2):
						r = '%s %s\r\n' % (edge.src, edge.dst)
						f.write(r)
		logger.info('Graphcache file created!')

	@staticmethod
	def load(dbsession, graph_id, graph_cache_dir, use_cache = True):
		logger.info('Loading Graphcache file to memory')
		graph_file = graph_cache_dir.joinpath(JackDawDomainGraphIGraph.graph_file_name)
		g = JackDawDomainGraphIGraph(dbsession, graph_id, graph_dir=graph_cache_dir, use_cache=use_cache)

		with open(graph_file, 'r') as f:
			g.graph = igraph.Graph.Read_Edgelist(f, directed=True)

		g.setup()
		logger.info('Loaded Graphcache file to memory OK')
		return g

	def has_path(self, src_sid, dst_sid):
		dst = self.__resolve_sid_to_id(dst_sid)
		if dst is None:
			raise Exception('SID not found!')

		src = self.__resolve_sid_to_id(src_sid)
		if src is None:
			raise Exception('SID not found!')
		
		res = self.graph.get_shortest_paths(src, to=dst, mode=igraph.ALL)
		for path in res:
			if len(path) != 0:
				return True
		return False

	def shortest_paths(self, src_sid = None, dst_sid = None, ignore_notfound = False, exclude = [], pathonly = False, maxhops = None):
		logger.info('shortest_paths called!')
		nv = GraphData()
		if pathonly is True:
			nv = []
		try:
			if src_sid is None and dst_sid is None:
				raise Exception('src_sid or dst_sid must be set')
			
			res = None
			if self.use_cache is True:
				res = self.read_cachefile(src_sid, dst_sid)

			if src_sid is None and dst_sid is not None:
				dst = self.__resolve_sid_to_id(dst_sid)
				if dst is None:
					raise Exception('SID not found!')
				
				if res is None:
					paths = self.graph.get_shortest_paths(dst, mode=igraph.IN)
					res = []
					for path in paths:
						if len(path) == 0:
							continue
						res.append(path[::-1])
					if self.use_cache is True:
						self.write_cachefile(src_sid, dst_sid, res)
				
				for path in res:
					self.__result_path_add(nv, path[:maxhops], exclude = exclude, pathonly = pathonly)

			elif src_sid is not None and dst_sid is not None:
				dst = self.__resolve_sid_to_id(dst_sid)
				if dst is None:
					raise Exception('SID not found!')

				src = self.__resolve_sid_to_id(src_sid)
				if src is None:
					raise Exception('SID not found!')

				try:
					if res is None:
						paths = self.graph.get_shortest_paths(src, to=dst, mode=igraph.OUT)
						res = []
						for path in paths:
							if len(path) == 0:
								continue
							res.append(path)
						if self.use_cache is True:
							self.write_cachefile(src_sid, dst_sid, res)
					
					for path in res:
						self.__result_path_add(nv, path, exclude = exclude, pathonly = pathonly)
				except Exception as e:
					raise e
					#pass

			elif src_sid is not None and dst_sid is None:
				src = self.__resolve_sid_to_id(src_sid)
				if src is None:
					raise Exception('SID not found!')
				
				try:
					if res is None:
						paths = self.graph.get_shortest_paths(src, mode=igraph.OUT)
						res = []
						for path in paths:
							if len(path) == 0:
								continue
							res.append(path)

						if self.use_cache is True:
							self.write_cachefile(src_sid, dst_sid, res)
					for path in res:
						self.__result_path_add(nv, path[:maxhops], exclude = exclude, pathonly = pathonly)
				except Exception as e:
					raise e
					#pass
				
			else:
				raise Exception('Not implemented!')
			
			logger.info('shortest_paths finished OK!')
			return nv
		except Exception as e:
			logger.info('shortest_paths finished ERR!')
			traceback.print_exc()
			if ignore_notfound is True:
				return nv
			raise

	
	def __resolve_sid_to_id(self, sid):
		for domain_id in self.adids:
			for res in self.dbsession.query(EdgeLookup.id).filter_by(ad_id = domain_id).filter(EdgeLookup.oid == sid).first():
				return res
		return None

	def __result_path_add(self, network, path, exclude = [], pathonly = False):
		if pathonly is False:
			for i in range(len(path) - 1):
				self.__result_edge_add(network, int(path[i]), int(path[i+1]), path, exclude = exclude)
		else:
			res = [[]]
			nolabel = False
			for i in range(len(path) - 1):
				for r in res:
					r.append(self.__nodename_to_sid(int(path[i])))
				labels = []
				for label in self.__resolv_edge_types(int(path[i]), int(path[i+1])):
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
				r.append(self.__nodename_to_sid(int(path[-1])))
			
			
			network += res
	
	def __add_nodes_from_path(self, network, path):
		if path == []:
			return
		path = [i for i in path]
		#delete_this = []
		for d, node_id in enumerate(path):
			sid, otype = self.__nodename_to_sid(node_id)
		
			if sid not in self.sid_adid_lookup:
				res = self.dbsession.query(EdgeLookup).filter_by(oid = sid).first()
				self.sid_adid_lookup[sid] = res.ad_id
			
			domain_id = self.sid_adid_lookup[sid]
			owned, highvalue = self.__get_props(sid)
			#delete_this.append('%s(%s) -> ' % (sid, otype))
			network.add_node(
				sid, 
				name = self.__sid2cn(sid, otype), 
				node_type = otype,
				domainid = domain_id,
				owned = owned,
				highvalue = highvalue
			)
			network.nodes[sid].set_distance(len(path)-d-1)


	def __result_edge_add(self, network, src_id, dst_id, path, exclude = []):
		for label in self.__resolv_edge_types(src_id, dst_id):
			if label not in exclude:
				try:
					src = self.__nodename_to_sid(src_id)
					dst = self.__nodename_to_sid(dst_id)
					if network.node_present(src) is False or network.node_present(dst) is False:
						self.__add_nodes_from_path(network, path)
						network.add_edge(src[0],dst[0], label=label)

					network.add_edge(src[0],dst[0], label=label)
				except Exception as e:
					import traceback
					traceback.print_exc()
					print(e)
					raise e
	
	def __nodename_to_sid(self, node_name):
		node_name = int(node_name)
		if node_name in self.name_sid_lookup:
			return self.name_sid_lookup[node_name]
		t = self.dbsession.query(EdgeLookup).get(node_name) #node_name is the ID of the edgelookup
		self.name_sid_lookup[node_name] = (t.oid, t.otype)
		return t.oid, t.otype

	def __get_props(self, oid):
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

	
	def __resolv_edge_types(self, src_id, dst_id):
		key = '%s_%s' % (str(src_id), str(dst_id))
		if key not in self.label_lookup:
			self.label_lookup[key] = []
			for domain_id in self.adids:
				for res in self.dbsession.query(Edge.label).distinct(Edge.label).filter_by(graph_id = self.graph_id).filter(Edge.ad_id == domain_id).filter(Edge.src == src_id).filter(Edge.dst == dst_id).all():
					self.label_lookup[key].append(res[0])
		
		for label in self.label_lookup[key]:
			yield label

	def __resolve_sid_to_id(self, sid):
		#print('__resolve_sid_to_id sid %s' % sid)
		for domain_id in self.adids:
			for res in self.dbsession.query(EdgeLookup.id).filter_by(ad_id = domain_id).filter(EdgeLookup.oid == sid).first():
				#print('__resolve_sid_to_id res %s' % res)
				return res
		return None


	def __sid2cn(self, sid, otype):
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
		
			else:
				print('__sid2cn unknown otype "%s" for sid %s' % (otype, sid))
				self.sid_name_lookup[sid] = None
		
		return self.sid_name_lookup[sid]

	def get_domainsids(self):
		pass

	def get_nodes(self):
		pass

	def get_distances_from_node(self):
		pass