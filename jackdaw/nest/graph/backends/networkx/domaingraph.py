
from gzip import GzipFile
import pathlib
import multiprocessing as mp
import networkx as nx
from bidict import bidict
from jackdaw import logger
from jackdaw.dbmodel.adtrust import JackDawADTrust
from jackdaw.dbmodel.adcomp import JackDawADMachine
from jackdaw.dbmodel.aduser import JackDawADUser
from jackdaw.dbmodel.adgroup import JackDawADGroup
from jackdaw.dbmodel.adinfo import JackDawADInfo
from jackdaw.nest.graph.graphdata import GraphData, GraphNode
from jackdaw.nest.graph.construct import GraphConstruct
from jackdaw.wintypes.well_known_sids import get_name_or_sid, get_sid_for_name
import threading

def short_worker(inqueue, outqueue, graph, dst_sid):
	"""
	Calculates the shortest parth for a given destination node
	This function is "multiprocessed"
	"""
	while True:
		node = inqueue.get()
		if node is None:
			outqueue.put(None)
			return
		try:
			for path in nx.all_shortest_paths(graph, source = node, target = dst_sid):
				outqueue.put(path)
									
		except nx.exception.NetworkXNoPath:
			continue

def short_node_gen(graph, inqueue, dst_sid, procno):
	"""
	Adding all nodes from the graph to the inqueue. At the end it adds terminating object in the amount of proccount.
	This function will be threaded. 
	"""
	for node in graph.nodes:
		if node == dst_sid:
			continue
		inqueue.put(node)
			
	for _ in range(procno):
		inqueue.put(None)


class JackDawDomainGraphNetworkx:
	def __init__(self, session, work_dir, construct = None):
		self.work_dir = work_dir
		self.graph = None
		self.session = session
		self.domain_sid = None
		self.domain_id = None
		self.__work_path = None
		self.__edges_file_path = None
		self.__resolv_table = bidict()
		self.construct = construct

	def save(self):
		pass

	def load(self, storedid):
		try:
			storedid = str(int(storedid))
		except Exception as e:
			raise e
		
		self.graph = nx.DiGraph()
		self.__work_path = pathlib.Path(self.work_dir).joinpath(storedid)
		self.__map_file_path = self.__work_path.joinpath('maps.gz')
		self.__edges_file_path = self.__work_path.joinpath('edges.gz')

		with GzipFile(self.__map_file_path, 'rb') as f:
			for line in f:
				line = line.strip()
				line = line.decode()
				sid, gid = line.split(',')
				self.__resolv_table[sid] = gid


		cnt = 0
		with GzipFile(self.__edges_file_path,'rb') as f:
			for line in f:
				line = line.strip()
				line = line.decode()
				src, dst, label, adid = line.split(',')
				construct = GraphConstruct(adid)
				if self.domain_sid is None:
					t = self.session.query(JackDawADInfo).get(adid)
					self.domain_sid = t.objectSid
					self.domain_id = adid
				self.__add_edge(src, dst, construct, label = label)
				cnt += 1

		logger.info('Done! %s' % cnt)

	def all_shortest_paths(self, src_sid = None, dst_sid = None):
		nv = GraphData()
		
		if not src_sid and not dst_sid:
			raise Exception('Either source or destination MUST be specified')
		
		elif not src_sid and dst_sid:
			try:
				dst_sid = self.__resolv_table[dst_sid]
				print(dst_sid)
				#for each node we calculate the shortest path to the destination node, silently skip the ones who do not have path to dst
				inqueue = mp.Queue()
				outqueue = mp.Queue()
				procno = mp.cpu_count()
				logger.debug('[DST_CALC] Starting processes')
				procs = [mp.Process(target = short_worker, args = (inqueue, outqueue, self.graph, dst_sid)) for i in range(procno)]			
				for proc in procs:
					proc.daemon = True
					proc.start()
				logger.debug('[DST_CALC] Starting generator thread')
				node_gen_th = threading.Thread(target = short_node_gen, args = (self.graph, inqueue, dst_sid, procno))
				node_gen_th.daemon = True
				node_gen_th.start()

				p_cnt = 0
				while True:
					path = outqueue.get()
					if path is None:
						procno -= 1
						logger.debug('[DST_CALC] Proc X - Finished!')
						if procno == 0:
							break
						continue
					self.__add_path(nv, path)
					p_cnt += 1

				logger.debug('[DST_CALC] Found %s paths to dst node %s' % (p_cnt, dst_sid))

				logger.debug('[DST_CALC] joining processes')
				for proc in procs:
					proc.join()
				logger.debug('[DST_CALC] Finished!')

			except:
				logger.exception('[DST_CALC]')
			
		elif src_sid and not dst_sid:
			#for each node we calculate the shortest path to the destination node, silently skip the ones who do not have path to dst
			src_sid = self.__resolv_table[src_sid]
			for node in self.graph.nodes:
				if node == src_sid:
					continue
				try:
					for path in nx.all_shortest_paths(self.graph, source = src_sid, target = node):
						self.__add_path(nv, path)
									
				except nx.exception.NetworkXNoPath:
					continue
					
		else:
			src_sid = self.__resolv_table[src_sid]
			dst_sid = self.__resolv_table[dst_sid]
			#for each node we calculate the shortest path to the destination node, silently skip the ones who do not have path to dst
			for path in nx.all_shortest_paths(self.graph, source = src_sid, target = dst_sid):
				self.__add_path(nv, path)
		
		return nv

	def get_domainsids(self):
		pass

	def get_nodes(self):
		pass

	def get_distances_from_node(self):
		pass

	
	def __add_path(self, network, path):
		"""
		Adds the path to the representational network
		Path is a list of sids (nodes), so we need to find the edges matching
		"""
		for d, sid in enumerate(path):
			true_sid = self.__resolv_table.inverse[sid]
			network.add_node(
				true_sid, 
				name = self.graph.nodes[sid].get('name', self.sid2cn(sid)), 
				node_type = self.graph.nodes[sid].get('node_type'),
				domainid = self.graph.nodes[sid]['construct'].ad_id
			)
			network.nodes[true_sid].set_distance(d)
		
		for i in range(len(path) - 1):
			for edge in self.graph.edges([path[i], ], data=True):
				if edge[1] == path[i + 1]:
					name = edge[2].get('label', None)
					network.add_edge(self.__resolv_table.inverse[path[i]] , self.__resolv_table.inverse[path[i+1]], label=name)

	def __add_edge(self, sid_src, sid_dst, construct, label = None, weight = 1):
		if not sid_src or not sid_dst:
			return
		true_src = self.__resolv_table.inverse[sid_src]
		true_dst = self.__resolv_table.inverse[sid_dst]
		if construct.is_blacklisted_sid(true_src) or construct.is_blacklisted_sid(true_dst):
			return
			
		self.__add_sid_to_node(sid_src, 'unknown', construct)
		self.__add_sid_to_node(sid_dst, 'unknown', construct)
			
		self.graph.add_edge(sid_src, sid_dst, label = label, weight = weight)

	def __add_sid_to_node(self, node, node_type, construct, name = None):
		if construct.is_blacklisted_sid(node):
			return
		if not name:
			name = str(get_name_or_sid(str(node)))
		
		#this presence-filter is important, as we will encounter nodes that are known and present in the graph already
		#ald later will be added via tokengroups as unknown
		if node not in self.graph.nodes:
			self.graph.add_node(str(node), name=name, node_type=node_type, construct = construct)


	def sid2cn(self, sid, throw = False):
		tsid = self.session.query(JackDawADGroup.cn).filter(JackDawADGroup.sid == sid).first()
		if tsid is not None:
			return tsid[0]
		
		tsid = self.session.query(JackDawADUser.cn).filter(JackDawADUser.objectSid == sid).first()
		if tsid is not None:
			return tsid[0]
		
		tsid = self.session.query(JackDawADMachine.cn).filter(JackDawADMachine.objectSid == sid).first()
		if tsid is not None:
			return tsid[0]

		tsid = self.session.query(JackDawADTrust.cn).filter(JackDawADTrust.securityIdentifier == sid).first()
		if tsid is not None:
			return tsid[0]

		
		t = str(get_name_or_sid(str(sid)))
		if t == sid and throw == True:
			raise Exception('No CN found for SID = %s' % repr(sid))
		return t
	
	def cn2sid(self, cn, throw = False, domain_sid = None):
		sid = get_sid_for_name(cn, domain_sid)
		
		tsid = self.session.query(JackDawADGroup.objectSid).filter(JackDawADMachine.cn == cn).first()
		if tsid is not None:
			return tsid[0]
		
		tsid = self.session.query(JackDawADUser.objectSid).filter(JackDawADUser.cn == cn).first()
		if tsid is not None:
			return tsid[0]
		
		tsid = self.session.query(JackDawADMachine.objectSid).filter(JackDawADMachine.cn == cn).first()
		if tsid is not None:
			return tsid[0]

		tsid = self.session.query(JackDawADTrust.securityIdentifier).filter(JackDawADTrust.cn == cn).first()
		if tsid is not None:
			return tsid[0]
		
		if throw == True:
			raise Exception('No SID found for CN = %s' % repr(cn))
		return cn

	def get_node(self, nodeid = None):
		
		if nodeid is None:
			nodes = []
			for gid, props in list(self.graph.nodes(data=True)):
				nodes.append(GraphNode(gid, gid, props['construct'].ad_id )) #properties = {}))
			return nodes

		if nodeid not in self.graph.nodes:
			return None
		gid, props = self.graph.nodes[nodeid]
		return GraphNode(gid, gid, props['construct'].ad_id, properties = {})