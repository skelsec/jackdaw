from . import Basemodel, lf
import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, ForeignKey

class Credential(Basemodel):
	__tablename__ = 'credentials'

	id = Column(Integer, primary_key=True)
	user_id = Column(Integer, ForeignKey('users.id'))
	user = relationship("JackDawADUser", back_populates="credential")
	nt_hash = Column(String, index=True)
	lm_hash = Column(String, index=True)
	history_no = Column(Integer, index=True)

	@staticmethod
	def from_impacket(data):
		"""
		Remember that this doesnt populate the foreign keys!!! You'll have to do it separately!
		"""
		creds = []
		for line in data:
			cred = Credential()
			userdomainhist, flags, lm_hash, nt_hash, *t = line.split(':')
			#parsing history
			m = userdomainhist.find('_history')
			history_no = None
			if m != -1:
				history_no = int(userdomainhist.split('_history')[1])
				userdomainhist = userdomainhist.split('_history')[0]
			m = userdomainhist.find('\\')
			domain = '<LOCAL>'
			sAMAccountName = userdomainhist
			if m != -1:
				domain = userdomainhist.split('\\')[0]
				sAMAccountName = userdomainhist.split('\\')[1]
			cred.nt_hash = nt_hash
			cred.lm_hash = lm_hash
			cred.history_no = history_no
			creds.append((domain, sAMAccountName ,cred))

		return creds