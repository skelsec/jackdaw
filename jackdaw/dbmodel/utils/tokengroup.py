
import datetime
import json

class JackDawTokenGroup:
	
	def __init__(self):
		self.ad_id = None
		self.sid = None
		self.member_sid = None
		self.object_type = None
	

	@staticmethod
	def from_dict(d):
		t = JackDawTokenGroup()
		t.ad_id = d['ad_id']
		t.sid = d['sid']
		t.member_sid = d['member_sid']
		t.object_type = d['object_type']
		return t

	@staticmethod
	def from_json(x):
		return JackDawTokenGroup.from_dict(json.loads(x))

	def to_dict(self):
		return {
			'ad_id' : self.ad_id,
			'sid' : self.sid,
			'member_sid' : self.member_sid,
			'object_type' : self.object_type
		}

	def to_json(self):
		return json.dumps(self.to_dict())


	def to_graph_csv(self):
		return '%s,%s,%s,%s' % (self.sid, self.member_sid, self.object_type, self.ad_id)