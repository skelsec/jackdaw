import os
import pathlib
import platform
import copy

from jackdaw import logger
from jackdaw.dbmodel.edge import Edge
from jackdaw.dbmodel.edgelookup import EdgeLookup
from jackdaw.dbmodel import windowed_query
from jackdaw.nest.graph.graphdata import GraphData, GraphNode
from jackdaw.dbmodel.graphinfo import GraphInfo, GraphInfoAD
from jackdaw.nest.graph.backends.domaingraph import JackDawDomainGraph

import igraph
from tqdm import tqdm
from sqlalchemy import func
import traceback



class JackDawDomainGraphIGraph(JackDawDomainGraph):
	graph_file_name = 'networkx.csv' #it is the same format
	def __init__(self, dbsession, graph_id, graph_dir, use_cache = False):
		JackDawDomainGraph.__init__(self, dbsession, graph_id, graph_dir, use_cache = False)

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

			sf = str(sqlite_file)
			gf = str(graph_file)
			if platform.system() == 'Windows':
				sf = sf.replace('\\', '\\\\')
				gf = gf.replace('\\', '\\\\')
			qry_str = '.open %s\r\n.mode csv\r\n.output %s\r\n.separator " "\r\nSELECT src,dst FROM adedges, adedgelookup WHERE adedges.graph_id = %s AND adedgelookup.id = adedges.src AND adedgelookup.oid IS NOT NULL;\r\n.exit' % (sf, gf, graph_id)
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
	def load(dbsession, graph_id, graph_cache_dir, use_cache = False):
		logger.info('Loading Graphcache file to memory')
		graph_file = graph_cache_dir.joinpath(JackDawDomainGraphIGraph.graph_file_name)
		g = JackDawDomainGraphIGraph(dbsession, graph_id, graph_dir=graph_cache_dir, use_cache=use_cache)

		with open(graph_file, 'r') as f:
			g.graph = igraph.Graph.Read_Edgelist(f, directed=True)

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
		
		res = self.graph.get_shortest_paths(src, to=dst, mode=igraph.ALL)
		for path in res:
			if len(path) != 0:
				return True
		return False

	def shortest_paths(self, src_sid = None, dst_sid = None, ignore_notfound = False, exclude = [], pathonly = False, maxhops = None, all_shortest = False):
		logger.info('shortest_paths called!')
		nv = GraphData()
		if pathonly is True:
			nv = []
		try:
			if src_sid is None and dst_sid is None:
				raise Exception('src_sid or dst_sid must be set')
			
			res = None

			if src_sid is None and dst_sid is not None:
				dst = self.resolve_sid_to_id(dst_sid)
				if dst is None:
					raise Exception('SID not found!')
				
				if res is None:
					if all_shortest is True:
						paths = self.graph.get_all_shortest_paths(dst, mode=igraph.IN)
					else:
						paths = self.graph.get_shortest_paths(dst, mode=igraph.IN)
					res = []
					for path in paths:
						if len(path) == 0:
							continue
						res.append(path[::-1])
				
				for path in res:
					self.result_path_add(nv, path[:maxhops], exclude = exclude, pathonly = pathonly)

			elif src_sid is not None and dst_sid is not None:
				dst = self.resolve_sid_to_id(dst_sid)
				if dst is None:
					raise Exception('SID not found!')

				src = self.resolve_sid_to_id(src_sid)
				if src is None:
					raise Exception('SID not found!')

				try:
					if res is None:
						if all_shortest is True:
							paths = self.graph.get_all_shortest_paths(src, to=dst, mode=igraph.OUT)
						else:
							paths = self.graph.get_shortest_paths(src, to=dst, mode=igraph.OUT)
						res = []
						for path in paths:
							if len(path) == 0:
								continue
							res.append(path)
					
					for path in res:
						self.result_path_add(nv, path, exclude = exclude, pathonly = pathonly)
				except Exception as e:
					raise e
					#pass

			elif src_sid is not None and dst_sid is None:
				src = self.resolve_sid_to_id(src_sid)
				if src is None:
					raise Exception('SID not found!')
				
				try:
					if res is None:
						if all_shortest is True:
							paths = self.graph.get_all_shortest_paths(src, mode=igraph.OUT)
						else:
							paths = self.graph.get_shortest_paths(src, mode=igraph.OUT)
						res = []
						for path in paths:
							if len(path) == 0:
								continue
							res.append(path)

					for path in res:
						self.result_path_add(nv, path[:maxhops], exclude = exclude, pathonly = pathonly)
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