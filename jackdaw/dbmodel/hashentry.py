from . import Basemodel
import datetime
from sqlalchemy import Column, Integer, String, Boolean

class HashEntry(Basemodel):
	__tablename__ = 'hashes'
	
	id = Column(Integer, primary_key=True)
	nt_hash = Column(String, index = True)
	lm_hash = Column(String, index = True)
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
		self.nt_hash = nt_hash
		self.lm_hash = lm_hash

		self.plaintext = None
		self.pw_length = None
		self.pw_lower = None
		self.pw_upper = None
		self.pw_upper = None
		self.pw_digit = None
		self.pw_special = None

		self.set_stats(plaintext)
		

	def set_stats(self, plaintext):
		decoded = None
		if plaintext.startswith('$HEX['):
			for enc in ['latin-1', 'utf-16-le', 'utf8']:
				try:
					decoded = bytes.fromhex(plaintext[5:-1]).decode(enc)
					break
				except Exception as e:
					continue
		else:
			decoded = plaintext

		if decoded is None:
			raise Exception('Failed to decode: %s' % plaintext)

		self.plaintext = decoded
		self.pw_length = len(self.plaintext)
		self.pw_lower = any(c.islower() for c in self.plaintext)
		self.pw_upper = any(c.isupper() for c in self.plaintext)
		self.pw_upper = any(c.isupper() for c in self.plaintext)
		self.pw_digit = any(c in '0123456789' for c in self.plaintext)
		self.pw_special = any(HashEntry.isspecial(c) for c in self.plaintext)
	
	@staticmethod
	def from_potfile(potfile):
		with open(potfile, 'r') as f:
			for line in f:
				line = line.strip()
				
				some_hash, plaintext = line.split(':', 1)				
				if len(some_hash) == 32:
					yield HashEntry(plaintext, nt_hash = some_hash)
				elif len(some_hash) == 16:
					yield HashEntry(plaintext, lm_hash = some_hash)
				else:
					continue
			