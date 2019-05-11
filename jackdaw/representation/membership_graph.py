
from jackdaw.dbmodel.adinfo import JackDawADInfo
from jackdaw.dbmodel.tokengroup import JackDawTokenGroup
from jackdaw.dbmodel import *
from jackdaw.wintypes.well_known_sids import get_name_or_sid, get_sid_for_name

from pyvis.network import Network
import networkx as nx

OBJECTTYPE_GUID_MAP = {
    'group': 'bf967a9c-0de6-11d0-a285-00aa003049e2',
    'domain': '19195a5a-6da0-11d0-afd3-00c04fd930c9',
    'organizationalUnit': 'bf967aa5-0de6-11d0-a285-00aa003049e2',
    'user': 'bf967aba-0de6-11d0-a285-00aa003049e2',
    'groupPolicyContainer': 'f30e3bc2-9ff0-11d1-b603-0000f80367c1'
}

def ace_applies(ace_guid, object_class):
	'''
	Checks if an ACE applies to this object (based on object classes).
	Note that this function assumes you already verified that InheritedObjectType is set (via the flag).
	If this is not set, the ACE applies to all object types.
	'''
	try:
		our_ace_guid = OBJECTTYPE_GUID_MAP[object_class]
	except KeyError:
		return False
	if ace_guid == our_ace_guid:
		return True
	# If none of these match, the ACE does not apply to this object
	return False


class MembershipPlotter:
	def __init__(self, db_conn):
		self.db_conn = db_conn
		self.graph = nx.DiGraph()
		self.network_visual = Network("3000px", "3000px")
		self.show_group_memberships = True
		self.show_user_memberships = True
		self.show_machine_memberships = True
		self.show_session_memberships = True
		self.show_localgroup_memberships = False
		self.show_constrained_delegations = True
		self.show_unconstrained_delegations = True
		self.show_custom_relations = True
		self.unknown_node_color = "#ffffff"
		
		self.blacklist_sids = {'S-1-5-32-545': ''}
		self.ignoresids = {"S-1-3-0": '', "S-1-5-18": ''}
		
	def is_blacklisted_sid(self, sid):
		if sid in self.blacklist_sids:
			return True
		if sid[:len('S-1-5-21')] == 'S-1-5-21':
			if sid[-3:] == '513':
				return True
			
		return False
	
	def add_sid_to_node(self, node, name = None, color = None):
		if self.is_blacklisted_sid(node):
			return
		if not name:
			name = str(get_name_or_sid(str(node)))
		if not color:
			color = self.unknown_node_color
		
		if node not in self.graph.nodes:
			self.graph.add_node(str(node), name=name)
		
		if node not in self.network_visual.nodes:
			self.network_visual.add_node(str(node), label=name, color=color)
			
	def add_edge(self, sid_src, sid_dst, label = None, weight = 1):
		if not sid_src or not sid_dst:
			return
		if self.is_blacklisted_sid(sid_src) or self.is_blacklisted_sid(sid_dst):
			return
			
		self.graph.add_edge(sid_src, sid_dst, label = label, weight = weight)
		self.network_visual.add_edge(sid_src, sid_dst, label = label, weight = weight)
			
	def sid2cn(self, sid, throw = False):
		session = get_session(self.db_conn)
		tsid = session.query(JackDawTokenGroup.cn).filter(JackDawTokenGroup.sid == sid).first()
		print('sid2cn: %s' % tsid)
		if not tsid:
			t = str(get_name_or_sid(str(sid)))
			if t == sid and throw == True:
				raise Exception('No SID found for CN = %s' % repr(cn))
			return t
		return tsid[0]
	
	def cn2sid(self, cn, throw = False, domain_sid = None):
		
		sid = get_sid_for_name(cn, domain_sid)
		
	
		session = get_session(self.db_conn)
		tsid = session.query(JackDawTokenGroup.sid).filter(JackDawTokenGroup.cn == cn).first()
		print(tsid)
		if not tsid:
			if throw == True:
				raise Exception('No SID found for CN = %s' % repr(cn))
			return cn
		return tsid[0]
			
			
	def show_path(self, src_cn, dst_cn, domain_sid = None):
		
		src_sid = self.cn2sid(src_cn, True, domain_sid)	
		dst_sid = self.cn2sid(dst_cn, True, domain_sid)	
	
		nv = Network("1000px", "1000px")
		
		for a in nx.all_shortest_paths(self.graph, source = src_sid, target = dst_sid):
			#print(a)
			#print(a[0])
			
			for sid in a:
				nv.add_node(sid, label = self.sid2cn(sid))
			
			for i in range(len(a) - 1):
				for edge in self.graph.edges([a[i], ], data=True):
					if edge[1] == a[i + 1]:
						name = edge[2].get('label', None)
						nv.add_edge(a[i], a[i + 1], label=name)
						print(edge)
					
			
		
		
		return nv
		
	def plot(self, network):
		"""
		Creates and opens an HTML file representing the network
		
		network: pyvis network
		"""
		network.show_buttons()
		network.show("test.html")
		
	def get_network_data(self, ad_id):
		"""
		Fills the network graph from database to memory
		"""
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
				self.add_sid_to_node(group.sid, name=group.name, color="#00ff1e")
		
		#distinct_filter = {}
		if self.show_user_memberships == True:
			#adding user nodes
			for user in adinfo.users:
				self.add_sid_to_node(user.objectSid, name=user.sAMAccountName, color="#162347")
				
		distinct_filter = {}
		if self.show_machine_memberships == True:
			#adding user nodes
			for user in adinfo.computers:
				if user.objectSid in distinct_filter:
					continue
				distinct_filter[user.objectSid] = 1
				self.add_sid_to_node(user.objectSid, name=user.sAMAccountName, color="#dd4b39")
		
		
		if self.show_session_memberships == True:
			for res in session.query(JackDawADUser.objectSid, JackDawADMachine.objectSid).filter(NetSession.username == JackDawADUser.sAMAccountName).filter(NetSession.source == JackDawADMachine.sAMAccountName).distinct(NetSession.username):
				self.add_edge(res[0], res[1], label='hasSession')
		
		if self.show_localgroup_memberships == True:
			#TODO: maybe create edges based on local username similarities??
			for res in session.query(JackDawADUser.objectSid, JackDawADMachine.objectSid, LocalGroup.groupname).filter(LocalGroup.username == JackDawADUser.sAMAccountName).filter(LocalGroup.hostname == JackDawADMachine.sAMAccountName):
				label = None
				if res[3] == 'Remote Desktop Users':
					label = 'canRDP'
					weight = 1
					
				elif res[3] == 'Distributed COM Users':
					label = 'executeDCOM'
					weight = 1
					
				elif res[3] == 'Administrators':
					label = 'adminTo'
					weight = 1
					
				self.add_edge(res[0], res[1], label=label, weight = weight)
			
		if self.show_constrained_delegations == True:
			pass
			
			
		if self.show_unconstrained_delegations == True:
			pass
			
		if self.show_custom_relations == True:
			for res in adinfo.customrelations:
				self.add_edge(res.sid, res.target_sid)
			
		
		#adding membership edges
		for tokengroup in adinfo.group_lookups:
			self.add_sid_to_node(tokengroup.sid)
			self.add_sid_to_node(tokengroup.member_sid)
				
			if tokengroup.is_user == True and self.show_user_memberships == True:
				try:
					self.add_edge(tokengroup.sid, tokengroup.member_sid, label='member')
				except AssertionError as e:
					print(e)
			elif tokengroup.is_machine == True and self.show_machine_memberships == True:
				try:
					self.add_edge(tokengroup.sid, tokengroup.member_sid, label='member')
				except AssertionError as e:
					print(e)
			elif tokengroup.is_group == True and self.show_group_memberships == True:
				try:
					self.add_edge(tokengroup.sid, tokengroup.member_sid, label='member')
				except AssertionError as e:
					print(e)
					
		#adding ACL edges
		for acl in adinfo.objectacls:
			##SUPER-IMPORTANT!!!!
			##THE ACCESS RIGHTS CALCULATIONS ARE FLAWED (JUST LIKE IN BLOODHOUND)
			##CORRECT WAY WOULD BE TO TRAVERSE ALL ACES IN A GIVEN ACL IN THE ORDER OF "ACE-ODER" AND CHECK FOR DENY POLICIES AS WELL!!!
			##TODO: CALCULATE THE EFFECTIVE PERMISSIONS IN A CORRECT MANNER :)
			
			##TODO: The DB is designed that most of these calculations can (and should) be offloaded to the DB itself
			##      Currently it's in python bc I'm laze and Dirkjan already wrote the major part
			##      https://github.com/fox-it/BloodHound.py/blob/0d3897ba4cc00818c0fc3e01fa3a91fc42e799e2/bloodhound/enumeration/acls.py
			
			if acl.owner_sid not in self.ignoresids:
				self.add_edge(acl.owner_sid, acl.sid, label='Owner')
				
			if acl.ace_sid in self.ignoresids:
				continue
			
			if acl.ace_objecttype in ['ACCESS_ALLOWED_ACE_TYPE','ACCESS_ALLOWED_OBJECT_ACE_TYPE']:
				if acl.ace_objecttype == 'ACCESS_ALLOWED_ACE_TYPE':
					if acl.ace_mask_generic_all == True:
						self.add_edge(acl.ace_sid, acl.sid, label='GenericALL')
					
					if acl.ace_mask_generic_write == True:
						self.add_edge(acl.ace_sid, acl.sid, label='GenericWrite')
						
					if acl.ace_mask_write_owner == True:
						self.add_edge(acl.ace_sid, acl.sid, label='WriteOwner')
						
					if acl.ace_mask_write_dacl == True:
						self.add_edge(acl.ace_sid, acl.sid, label='WriteDacl')
						
					if acl.object_type in ['user', 'domain'] and acl.ace_mask_control_access == True:
						self.add_edge(acl.ace_sid, acl.sid, label='ExtendedRightALL')
				
				if acl.ace_objecttype == 'ACCESS_ALLOWED_OBJECT_ACE_TYPE':
					if acl.ace_hdr_flag_inherited == True and acl.ace_hdr_flag_inherit_only == True:
						continue
					
					if acl.ace_hdr_flag_inherited == True and acl.ace_inheritedobjecttype is not None:
						if not ace_applies(acl.ace_inheritedobjecttype, acl.object_type):
							continue
					
					if any([acl.ace_mask_generic_all, acl.ace_mask_write_dacl, acl.ace_mask_write_owner, acl.ace_mask_generic_write]):
						if acl.ace_objecttype is not None and not ace_applies(acl.ace_objecttype, acl.object_type):
							continue
						
						if acl.ace_mask_generic_all == True:
							self.add_edge(acl.ace_sid, acl.sid, label='GenericALL')
							continue
				
						if acl.ace_mask_generic_write == True:
							self.add_edge(acl.ace_sid, acl.sid, label='GenericWrite')
							
						if acl.object_type != 'domain':
							continue
							
						if acl.ace_mask_write_dacl == True:
							self.add_edge(acl.ace_sid, acl.sid, label='WriteDacl')
							
						if acl.ace_mask_write_owner == True:
							self.add_edge(acl.ace_sid, acl.sid, label='WriteOwner')
							
					if acl.ace_mask_write_prop == True:
						if acl.object_type in ['user','group'] and acl.ace_objecttype is None:
							self.add_edge(acl.ace_sid, acl.sid, label='GenericWrite')
							
						if acl.object_type == 'group' and acl.ace_objecttype == 'bf9679c0-0de6-11d0-a285-00aa003049e2':
							self.add_edge(acl.ace_sid, acl.sid, label='AddMember')
							
						
				
					if acl.ace_mask_control_access == True:
						if acl.object_type in ['user','group'] and acl.ace_objecttype is not None:
							self.add_edge(acl.ace_sid, acl.sid, label='ExtendedAll')
						
						if acl.object_type == 'domain' and acl.ace_objecttype == '1131f6ad-9c07-11d1-f79f-00c04fc2dcd2':
							# 'Replicating Directory Changes All'
							self.add_edge(acl.ace_sid, acl.sid, label='GetChangesALL')
								
						if acl.object_type == 'domain' and acl.ace_objecttype == '1131f6aa-9c07-11d1-f79f-00c04fc2dcd2':
								# 'Replicating Directory Changes'
								self.add_edge(acl.ace_sid, acl.sid, label='GetChanges')
								
						if acl.object_type == 'user' and acl.ace_objecttype == '00299570-246d-11d0-a768-00aa006e0529':
								# 'Replicating Directory Changes'
								self.add_edge(acl.ace_sid, acl.sid, label='User-Force-Change-Password')
						
				
					