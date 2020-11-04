from . import Basemodel
import datetime
from sqlalchemy import Column, Integer, String, DateTime
from jackdaw.dbmodel.utils.serializer import Serializer

class DNSLookup(Basemodel, Serializer):
	__tablename__ = 'dnslookup'
	
	id = Column(Integer, primary_key=True)
	ad_id = Column(Integer, index=True)
	fetched_at = Column(DateTime, default=datetime.datetime.utcnow)
	sid = Column(String, index=True)
	ip = Column(String, index=True)
	domainname = Column(String, index=True)

	def __init__(self, ad_id, sid, ip, domain, fetched_at = None):
		self.ad_id = ad_id
		self.ip = str(ip)
		self.sid = str(sid)
		self.domainname = str(domain)
		self.fetched_at = fetched_at
		if self.fetched_at is None:
			self.fetched_at = datetime.datetime.utcnow()