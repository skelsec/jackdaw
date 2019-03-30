
from jackdaw.dbmodel.adinfo import JackDawADInfo
from jackdaw.dbmodel.tokengroup import JackDawTokenGroup
from jackdaw.dbmodel import *

from pyvis.network import Network
import networkx as nx

class MembershipPlotter:
	def __init__(self, db_conn):
		self.db_conn = db_conn
		self.graph = nx.Graph()
		self.show_group_memberships = True
		self.show_user_memberships = True
		self.show_machine_memberships = True
		self.show_session_memberships = True
		self.show_localgroup_memberships = True
		self.show_constrained_delegations = True
		self.show_unconstrained_delegations = True
		self.show_custom_relations = True
	
		
	def run(self, ad_id):
		session = get_session(self.db_conn)
		adinfo = session.query(JackDawADInfo).get(ad_id)
		
		node_lables = {}
		node_color_map = []
		
		distinct_filter = {}
		if self.show_group_memberships == True:
			#adding group nodes
			for group in adinfo.groups:
				if group.sid in distinct_filter:
					continue
				distinct_filter[group.sid] = 1
				self.graph.add_node(group.sid, name=group.name, guid=group.guid)
				node_lables[group.sid] = group.name
				#node_color_map.append('r')
				#self.graph.add_node(group.sid, label=group.name, color="#00ff1e")
		
		#distinct_filter = {}
		if self.show_user_memberships == True:
			#adding user nodes
			for user in adinfo.users:
				#if user.objectSid in distinct_filter:
				#	continue
				#distinct_filter[user.objectSid] = 1
				
				self.graph.add_node(user.objectSid, name= user.sAMAccountName)
				node_lables[user.objectSid] = user.sAMAccountName
				
		distinct_filter = {}
		if self.show_machine_memberships == True:
			#adding user nodes
			for user in adinfo.computers:
				if user.objectSid in distinct_filter:
					continue
				distinct_filter[user.objectSid] = 1
				self.graph.add_node(user.objectSid, name= user.sAMAccountName)
				node_lables[user.objectSid] = user.sAMAccountName
		
		
		if self.show_session_memberships == True:
			for res in session.query(JackDawADUser.objectSid, JackDawADMachine.objectSid).filter(NetSession.username == JackDawADUser.sAMAccountName).filter(NetSession.source == JackDawADMachine.sAMAccountName).distinct(NetSession.username):
				print(res)
				self.graph.add_edge(res[0], res[1])
		#return
		
		if self.show_localgroup_memberships == True:
			#TODO: maybe create edges based on local username similarities??
			
			for res in session.query(JackDawADUser.objectSid, JackDawADMachine.objectSid).filter(LocalGroup.username == JackDawADUser.sAMAccountName).filter(LocalGroup.hostname == JackDawADMachine.sAMAccountName).distinct(LocalGroup.username):
				self.graph.add_edge(res[0], res[1])
			pass
			
			#LocalGroup(Basemodel):
			#__tablename__ = 'localgroup'
			#
			#id = Column(Integer, primary_key=True)
			#fetched_at = Column(DateTime, default=datetime.datetime.utcnow)
			#ip = Column(String, index=True)
			#rdns = Column(String, index=True)
			#sid = Column(String, index=True)
			#sidusage = Column(String, index=True)
			#domain = Column(String, index=True)
			#username = Column(String, index=True)
			#groupname = Column(String, index=True)
			#......................................................
			#source = Column(String, index=True)
			#ip = Column(String, index=True)
			#rdns = Column(String, index=True)
			#username = Column(String, index=True)
			
		if self.show_constrained_delegations == True:
			pass
			
			
		if self.show_unconstrained_delegations == True:
			pass
			
		if self.show_custom_relations == True:
			for res in adinfo.customrelations:
				self.graph.add_edge(res.sid, res.target_sid)
			
		
		#adding membership edges
		for tokengroup in adinfo.group_lookups:		
			if tokengroup.is_user == True and self.show_user_memberships == True:
				try:
					self.graph.add_edge(tokengroup.sid, tokengroup.member_sid)
				except AssertionError as e:
					print(e)
			elif tokengroup.is_machine == True and self.show_machine_memberships == True:
				try:
					self.graph.add_edge(tokengroup.sid, tokengroup.member_sid)
				except AssertionError as e:
					print(e)
			elif tokengroup.is_group == True and self.show_group_memberships == True:
				try:
					self.graph.add_edge(tokengroup.sid, tokengroup.member_sid)
				except AssertionError as e:
					print(e)
		
		"""		
		#a = nx.shortest_path(self.graph, source = 'S-1-5-21-822153653-3397465503-3450368293-25829', target = 'S-1-5-21-822153653-3397465503-3450368293-22595')
		#print(a)
		#return 
		for x in nx.all_shortest_paths(self.graph, source = 'S-1-5-21-822153653-3397465503-3450368293-25829', target = 'S-1-5-21-822153653-3397465503-3450368293-512'):
			print(x)
		return
		sp = nx.shortest_path(self.graph, source = 'S-1-5-21-822153653-3397465503-3450368293-25829')
		for source in sp:
			t = []
			for target in sp[source]:
				dn = session.query(JackDawTokenGroup.dn).filter(JackDawTokenGroup.sid == target).first()
				try:
					t.append(dn[0])
				except Exception as e:
					t.append(target)
					#print(dn)
					#print(target)
					continue
			print('%s: %s' % (source, ' -> '.join(t)))
			
		#print(a)
		return		
		"""
		n = Network()
		n.from_nx(self.graph)
		n.show("test.html")