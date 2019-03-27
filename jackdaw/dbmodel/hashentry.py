from . import Basemodel
import datetime
from sqlalchemy import Column, Integer, String

class HashEntry(Basemodel):
	__tablename__ = 'hashes'
	
	id = Column(Integer, primary_key=True)
	nt_hash = Column(String, index = True)
	lm_hash = Column(String, index = True)
	plaintext = Column(String, index = True)

	def __init__(self, plaintext, nt_hash = None, lm_hash = None):
		self.plaintext = plaintext
		self.nt_hash = nt_hash
		self.lm_hash = lm_hash
	