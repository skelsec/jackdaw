from . import Basemodel
import datetime
from sqlalchemy import Column, Integer, String, DateTime
from jackdaw.dbmodel.utils.serializer import Serializer

class RDNSLookup(Basemodel, Serializer):
	__tablename__ = 'rdnslookup'
	
	id = Column(Integer, primary_key=True)
	ad_id = Column(Integer, index=True)
	fetched_at = Column(DateTime, default=datetime.datetime.utcnow)
	ip = Column(String, index=True)
	domain = Column(String, index=True)

	def __init__(self, ad_id, ip, domain, fetched_at = None):
		self.ad_id = ad_id
		self.ip = str(ip)
		self.domain = str(domain)
		self.fetched_at = fetched_at
		if self.fetched_at is None:
			self.fetched_at = datetime.datetime.utcnow()