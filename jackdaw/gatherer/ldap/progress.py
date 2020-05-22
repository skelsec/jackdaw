

class LDAPGathererProgress:
	def __init__(self):
		self.type = 'LDAP'
		self.msg_type = 'PROGRESS'
		self.adid = None
		self.domain_name = None
		self.finished = None
		self.running = None
		self.total_finished = None
		self.speed = None #per sec

	def __str__(self):
		if self.msg_type == 'PROGRESS':
			return '[%s][%s][%s][%s] FINISHED %s RUNNING %s TOTAL %s SPEED %s' % (
				self.type, 
				self.domain_name, 
				self.adid,
				self.msg_type,
				','.join(self.finished), 
				','.join(self.running), 
				self.total_finished, 
				self.speed
			
			)
		return '[%s][%s][%s][%s]' % (self.type, self.domain_name, self.adid, self.msg_type)