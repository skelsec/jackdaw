import enum

class GathererProgressType(enum.Enum):
	BASIC = 'LDAP_BASIC'
	SD = 'LDAP_SD'
	SDUPLOAD = 'LDAP_SD_UPLOAD'
	MEMBERS = 'LDAP_MEMBERS'
	MEMBERSUPLOAD = 'LDAP_MEMBERS_UPLOAD'
	SMB = 'SMB'
	SDCALC = 'SDCALC'
	SDCALCUPLOAD = 'SDCALCUPLOAD'
	INFO = 'INFO'
	REFRESH = 'REFRESH'

class MSGTYPE(enum.Enum):
	STARTED = 'STARTED'
	PROGRESS = 'PROGRESS'
	FINISHED = 'FINISHED'
	ERROR = 'ERROR'

class GathererProgress:
	def __init__(self):
		self.type = GathererProgressType.BASIC
		self.msg_type = MSGTYPE.PROGRESS
		self.adid = None
		self.domain_name = None
		self.total = None #total number of elements needs processing
		self.total_finished = None #finished number of elements
		self.step_size = None #how many new elements processed will trigger an update message
		self.speed = None #processed elements per second
		self.error = None #should be an exception, but string is okay

		#FOR BASIC
		self.finished = [] #list of tasks finished
		self.running = [] #list of tasks currently running
		

		#FOR SMB
		self.errors = None
		self.sessions = None
		self.shares = None
		self.groups = None

		#FOR INFO
		self.text = None


	def __str__(self):
		if self.msg_type == MSGTYPE.PROGRESS:
			return '[%s][%s][%s][%s] FINISHED %s RUNNING %s TOTAL %s SPEED %s' % (
				self.type.value, 
				self.domain_name, 
				self.adid,
				self.msg_type.value,
				','.join(self.finished), 
				','.join(self.running), 
				self.total_finished, 
				self.speed
			)
		return '[%s][%s][%s][%s]' % (self.type.value, self.domain_name, self.adid, self.msg_type.value)



class SMBEnumeratorProgress:
	def __init__(self):
		self.type = 'SMB'
		self.msg_type = 'PROGRESS'
		self.adid = None
		self.domain_name = None
		
		
	def __str__(self):
		if self.msg_type == 'PROGRESS':
			return '[%s][%s][%s][%s] HOSTS %s SHARES %s SESSIONS %s GROUPS %s ERRORS %s' % (
				self.type, 
				self.domain_name, 
				self.adid,
				self.msg_type,
				self.hosts, 
				self.shares, 
				self.sessions, 
				self.groups, 
				self.errors
			
			)
		
		return '[%s][%s][%s][%s]' % (self.type, self.domain_name, self.adid, self.msg_type)