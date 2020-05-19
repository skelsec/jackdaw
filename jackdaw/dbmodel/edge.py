from . import Basemodel
import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
import json

class JackDawEdge(Basemodel):
	__tablename__ = 'edges'
	
	id = Column(Integer, primary_key=True)
	ad_id = Column(Integer, ForeignKey('ads.id'))
	graph_id = Column(Integer, index = True)
	src = Column(Integer, index = True)
	dst = Column(Integer, index = True)
	label = Column(String, index = True)

	def __init__(self, ad_id, graph_id, src, dst, label):
		self.ad_id = int(ad_id)
		self.graph_id = graph_id
		self.src = int(src)
		self.dst = int(dst)
		self.label = label

	@staticmethod
	def from_dict(d):
		return JackDawEdge(d['ad_id'], d['graph_id'], d['src'], d['dst'], d['label'])

	@staticmethod
	def from_json(x):
		return JackDawEdge.from_dict(json.loads(x))

	def to_dict(self):
		return {
			'ad_id' : self.ad_id,
			'graph_id' : self.graph_id,
			'src' : self.src,
			'dst' : self.dst,
			'label' : self.label
		}

	def to_json(self):
		return json.dumps(self.to_dict())
