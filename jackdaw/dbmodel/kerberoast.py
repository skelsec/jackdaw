from . import Basemodel
import datetime
from sqlalchemy import Column, Integer, String, DateTime
from jackdaw.dbmodel.utils.serializer import Serializer

class Kerberoast(Basemodel, Serializer):
	__tablename__ = 'kerberoast'
	
	id = Column(Integer, primary_key=True)
	ad_id = Column(Integer, index=True)
	user_id = Column(Integer, index=True)
	fetched_at = Column(DateTime, default=datetime.datetime.utcnow)
	ticket_type = Column(String, index=True)
	encryption = Column(Integer, index=True)
	ticket = Column(String)

	def __init__(self, ad_id, user_id, ticket_type, encryption, ticket, fetched_at = None):
		self.ad_id = ad_id
		self.user_id = user_id
		self.ticket_type = ticket_type
		self.encryption = encryption
		self.ticket = ticket
		if self.fetched_at is None:
			self.fetched_at = datetime.datetime.utcnow()

	@staticmethod
	def from_hash(ad_id, user_id, h):
		if h.startswith('$krb5asrep$'):
			ticket_type = 'asrep'
			t = h[11:]
		elif h.startswith('$krb5tgs$'):
			ticket_type = 'spnrep'
			t = h[9:]
		else:
			raise Exception('Unknown ticket type for %s' % str(h))
		
		encryption = int(t[:t.find('$')])
		return Kerberoast(ad_id, user_id, ticket_type, encryption, h)
		