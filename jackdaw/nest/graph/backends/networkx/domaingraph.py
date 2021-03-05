
import copy

from jackdaw import logger
from jackdaw.dbmodel.graphinfo import GraphInfo, GraphInfoAD
from jackdaw.dbmodel.edge import Edge
from jackdaw.dbmodel.edgelookup import EdgeLookup
from jackdaw.dbmodel import windowed_query
from jackdaw.nest.graph.graphdata import GraphData, GraphNode, NodeNotFoundException
from jackdaw.nest.graph.backends.domaingraph import JackDawDomainGraph

import networkx as nx
from networkx.algorithms.shortest_paths.generic import shortest_path, has_path, all_shortest_paths

from sqlalchemy import func
import platform
from tqdm import tqdm
if platform.system() == 'Emscripten':
	tqdm.monitor_interval = 0


class JackDawDomainGraphNetworkx(JackDawDomainGraph):
	graph_file_name = 'networkx.csv'
	def __init__(self, dbsession, graph_id, graph_dir, use_cache = False):
		JackDawDomainGraph.__init__(self, dbsession, graph_id, graph_dir, use_cache = False)

		#self.dbsession = session
		#self.graph_id = int(graph_id)
		#self.constructs = {}
		#self.graph = None
		#self.adids = []
		#self.name_sid_lookup = {}
		#self.props_lookup = {}
		#self.sid_adid_lookup = {}
		#self.sid_name_lookup = {}
		#self.label_lookup = {}
		#self.use_cache = use_cache
		#self.graph_dir = graph_dir

	def write_cachefile(self, src_sid, dst_sid, paths):
		src_sid = str(src_sid)
		dst_sid = str(dst_sid)

		fname = '%s_%s.cache' % (src_sid, dst_sid)
		cache_file_path = self.graph_dir.joinpath(fname)
		with open(cache_file_path, 'w', newline = '') as f:
			if isinstance(paths, list):
				ps = ','.join([str(x) for x in paths]) + '\r\n'
				print(ps)
				f.write(ps)
			else:
				for src in paths:
					ps = ','.join([str(x) for x in paths[src]]) + '\r\n'
					print(ps)
					f.write(ps)
		print('Done!')
	
	def read_cachefile(self, src_sid, dst_sid):
		both = False
		if src_sid is not None and dst_sid is not None:
			both = True
		src_sid = str(src_sid)
		dst_sid = str(dst_sid)

		fname = '%s_%s.cache' % (src_sid, dst_sid)
		cache_file_path = self.graph_dir.joinpath(fname)
		try:
			res = {} if both is False else []
			with open(cache_file_path, 'r') as f:
				print('Found cache file for %s' % fname)
				for line in f:
					line=line.strip()
					if line == '':
						continue
					if both is True:
						res.append(line.split(','))
					else:
						path = [int(x) for x in line.split(',')]
						res[path[0]] = path
			return res
		except Exception as e:
			print(e)
			return None

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
		graph_file = graph_dir.joinpath(JackDawDomainGraphNetworkx.graph_file_name)

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

			sf = str(sqlite_file)
			gf = str(graph_file)
			if platform.system() == 'Windows':
				sf = sf.replace('\\', '\\\\')
				gf = gf.replace('\\', '\\\\')

			qry_str = '.open %s\r\n.mode csv\r\n.output %s\r\n.separator " "\r\nSELECT src,dst FROM adedges, adedgelookup WHERE adedges.graph_id = %s AND adedgelookup.id = adedges.src AND adedgelookup.oid IS NOT NULL;\r\n.exit' % (sf, gf, graph_id)
			with open('buildnode.sql', 'w') as f:
				f.write(qry_str)
			
			import subprocess
			import shlex
			
			cmd = 'cat buildnode.sql | sqlite3'
			if platform.system() == 'Windows':
				cmd = 'type buildnode.sql | sqlite3'

			process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
			stdout, stderr = process.communicate()
			process.wait()
			
			if process.returncode == 0:
				using_sqlite_tool = True
				logger.info('sqlite3 dumping method OK!')
			else:
				logger.warining('Failed to use the sqlite3 tool to speed up graph datafile generation. Reason: %s' % stderr)
				

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
		graph_file = graph_cache_dir.joinpath(JackDawDomainGraphNetworkx.graph_file_name)
		graph = nx.DiGraph()
		g = JackDawDomainGraphNetworkx(dbsession, graph_id, graph_dir=graph_cache_dir, use_cache=use_cache)
		g.graph = nx.read_edgelist(str(graph_file), nodetype=int, create_using=graph)
		g.setup()
		logger.info('Loaded Graphcache file to memory OK')
		return g

	def has_path(self, src_sid, dst_sid):
		dst = self.resolve_sid_to_id(dst_sid)
		if dst is None:
			raise Exception('SID not found!')

		src = self.resolve_sid_to_id(src_sid)
		if src is None:
			raise Exception('SID not found!')

		return has_path(self.graph, src, dst)
		

	def shortest_paths(self, src_sid = None, dst_sid = None, ignore_notfound = False, exclude = [], pathonly = False, maxhops = None, all_shortest = False):
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
				dst = self.resolve_sid_to_id(dst_sid)
				if dst is None:
					raise Exception('SID not found!')
				
				if res is None:
					res = shortest_path(self.graph, target=dst)
					if self.use_cache is True:
						self.write_cachefile(src_sid, dst_sid, res)
				
				for k in res:
					self.result_path_add(nv, res[k][:maxhops], exclude = exclude, pathonly = pathonly)

			elif src_sid is not None and dst_sid is not None:
				dst = self.resolve_sid_to_id(dst_sid)
				if dst is None:
					raise Exception('SID not found!')

				src = self.resolve_sid_to_id(src_sid)
				if src is None:
					raise Exception('SID not found!')

				try:
					if res is None:
						res = shortest_path(self.graph, src, dst)
						if self.use_cache is True:
							self.write_cachefile(src_sid, dst_sid, res)
					self.result_path_add(nv, res, exclude = exclude, pathonly = pathonly)
				except nx.exception.NetworkXNoPath:
					pass

			elif src_sid is not None and dst_sid is None:
				src = self.resolve_sid_to_id(src_sid)
				if src is None:
					raise Exception('SID not found!')
				
				try:
					if res is None:
						res = shortest_path(self.graph, src)
						if self.use_cache is True:
							self.write_cachefile(src_sid, dst_sid, res)
					for k in res:
						self.result_path_add(nv, res[k][:maxhops], exclude = exclude, pathonly = pathonly)
				except nx.exception.NetworkXNoPath:
					pass
				
			else:
				raise Exception('Not implemented!')
			
			logger.info('shortest_paths finished OK!')
			return nv
		except nx.exception.NodeNotFound:
			logger.info('shortest_paths finished ERR!')
			if ignore_notfound is True:
				return nv
			raise

	

	