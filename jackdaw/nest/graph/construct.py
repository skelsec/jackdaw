


class GraphConstruct:
	def __init__(self, ad_id, diff_name = None):
		self.ad_id = ad_id
		self.diff_name = diff_name # should be a string 'new' or 'old'
		
		self.include_nodes = []
		self.include_edges = []

		self.blacklist_sids = {'S-1-5-32-545': ''}
		self.ignoresids = {"S-1-3-0": '', "S-1-5-18": ''}


	def is_blacklisted_sid(self, sid):
		if sid in self.blacklist_sids:
			return True
		if sid[:len('S-1-5-21')] == 'S-1-5-21':
			if sid[-3:] == '513':
				return True
			
		return False

	@staticmethod
	def from_dict(d):
		g = GraphConstruct(d['ad_id'])
		g.diff_name = d['diff_name']
		
		#g.include_nodes = []
		#g.include_edges = []

		g.blacklist_sids = d['blacklist_sids']
		g.ignoresids = d['ignoresids']

		return g

	def to_dict(self):
		return {
			'ad_id' : self.ad_id,
			'diff_name' : self.diff_name, 
			'include_nodes': None, #TODO! FIX!
			'include_edges' : None, #TODO! FIX!
			'blacklist_sids' : self.blacklist_sids,
			'ignoresids' : self.ignoresids
		}