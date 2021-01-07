from . import Basemodel, lf
import datetime
import hashlib
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, ForeignKey, Index, DateTime, Boolean

from jackdaw.dbmodel.utils.serializer import Serializer


class LSASecret(Basemodel, Serializer):
	__tablename__ = 'lsasecret'

	id = Column(Integer, primary_key=True)
	ad_id = Column(Integer)
	machine_sid = Column(String, nullable= False, default = '-1')
	secret_type = Column(String, index=True, nullable = False)
	secret = Column(String, index=False, nullable = False)

	def __init__(self, secret_type = None, secret = None, ad_id = -1, machine_sid = -1):
		self.ad_id = ad_id
		self.machine_sid = machine_sid
		self.secret_type = secret_type
		self.secret = secret

	@staticmethod
	def from_cached_secrets(cached_secrets, ad_id = -1, machine_sid = -1):
		for secret in cached_secrets:
			s = LSASecret()
			s.ad_id = ad_id
			s.machine_sid = machine_sid
			s.secret_type = str(type(secret))
			s.secret = str(secret)
			yield s