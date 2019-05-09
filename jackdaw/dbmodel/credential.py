from . import Basemodel, lf
import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, ForeignKey, Index

class Credential(Basemodel):
	__tablename__ = 'credentials'
	__table_args__ = (Index('Credential_uc', "domain", "username","nt_hash", "lm_hash", "history_no", unique = True), )

	id = Column(Integer, primary_key=True)
	#user_id = Column(Integer, ForeignKey('users.id'))
	#user = relationship("JackDawADUser", back_populates="credential", lazy = True)
	domain = Column(String, index=True, nullable= False)
	username = Column(String, index=True, nullable= False)
	nt_hash = Column(String, index=True, nullable= False)
	lm_hash = Column(String, index=True, nullable= False)
	history_no = Column(Integer, index=True, nullable= False)
	
	def __init__(self, domain = None, username = None, nt_hash = None, lm_hash = None, history_no = None):
		self.domain = domain
		self.username = username
		self.nt_hash = nt_hash
		self.lm_hash = lm_hash
		self.history_no = history_no

	@staticmethod
	def from_impacket_file(filename):
		"""
		Remember that this doesnt populate the foreign keys!!! You'll have to do it separately!
		important: historyno will start at 0. This means all history numbers in the file will be incremented by one
		"""
		with open(filename, 'r') as f:
			for line in f:
				cred = Credential()
				userdomainhist, flags, lm_hash, nt_hash, *t = line.split(':')
				#parsing history
				m = userdomainhist.find('_history')
				history_no = 0
				if m != -1:
					history_no = int(userdomainhist.split('_history')[1]) + 1
					userdomainhist = userdomainhist.split('_history')[0]
				m = userdomainhist.find('\\')
				domain = '<LOCAL>'
				username = userdomainhist
				if m != -1:
					domain = userdomainhist.split('\\')[0]
					username = userdomainhist.split('\\')[1]
				cred.nt_hash = nt_hash
				cred.lm_hash = lm_hash
				cred.history_no = history_no
				cred.username = username
				cred.domain = domain
				yield cred