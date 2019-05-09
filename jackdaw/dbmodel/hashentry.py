from . import Basemodel
import datetime
from sqlalchemy import Column, Integer, String, Boolean

class HashEntry(Basemodel):
	__tablename__ = 'hashes'
	
	id = Column(Integer, primary_key=True)
	nt_hash = Column(String)
	lm_hash = Column(String)
	plaintext = Column(String, unique = True, nullable= False)
	pw_length = Column(Integer, index = True)
	pw_lower = Column(Boolean, index = True)
	pw_upper = Column(Boolean, index = True)
	pw_digit = Column(Boolean, index = True)
	pw_special = Column(Boolean, index = True)
	
	

	def isspecial(s):
		if s.isupper() or s.islower() or s in '0123456789':
			return False
		return True

	def __init__(self, plaintext, nt_hash = None, lm_hash = None):
		self.plaintext = plaintext
		self.nt_hash = nt_hash
		self.lm_hash = lm_hash
		
		self.pw_length = len(plaintext)
		self.pw_lower = any(c.islower() for c in plaintext)
		self.pw_upper = any(c.isupper() for c in plaintext)
		self.pw_upper = any(c.isupper() for c in plaintext)
		self.pw_digit = any(c in '0123456789' for c in plaintext)
		self.pw_special = any(HashEntry.isspecial(c) for c in plaintext)
	
	@staticmethod
	def from_potfile(potfile):
		with open(potfile, 'r') as f:
			for line in f:
				line = line.strip()
				
				some_hash, plaintext = line.split(':', 1)
				if plaintext[:4] == 'HEX[':
					plaintext = bytes.fromhex(plaintext[4:-1]).decode()
				
				if len(some_hash) == 32:
					yield HashEntry(plaintext, nt_hash = some_hash)
				elif len(some_hash) == 16:
					yield HashEntry(plaintext, lm_hash = some_hash)
				else:
					continue
			