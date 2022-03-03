import enum

class GathererProgressType(enum.Enum):
	BASIC = 'LDAP_BASIC'
	SD = 'LDAP_SD'
	SDUPLOAD = 'LDAP_SD_UPLOAD'
	MEMBERS = 'LDAP_MEMBERS'
	MEMBERSUPLOAD = 'LDAP_MEMBERS_UPLOAD'
	SMB = 'SMB'
	SMBENUM = 'SMBENUM'
	KERBEROAST = 'KERBEROAST'
	SDCALC = 'SDCALC'
	SDCALCUPLOAD = 'SDCALCUPLOAD'
	INFO = 'INFO'
	REFRESH = 'REFRESH'
	USER = 'USER'
	MACHINE = 'MACHINE'
	SMBSHARE = 'SMBSHARE'
	SMBSESSION = 'SMBSESSION'
	SMBLOCALGROUP = 'SMBLOCALGROUP'
	DNS = 'DNS'
	GROUP = 'GROUP'

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
		self.graphid = None
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

		#FOR STREAMING
		self.data = None

	def get_percentage(self):
		if self.total is not None and self.total_finished is not None:
			p = (int(self.total_finished)/int(self.total))*100
			return '%.2f %%' % p
		return 'NA'

	def __str__(self):
		if self.type == GathererProgressType.BASIC:
			if self.msg_type == MSGTYPE.PROGRESS:
				return '[%s][%s][%s][%s] FINISHED %s RUNNING %s GATHERED %s SPEED %s obj/s' % (
					self.type.value, 
					self.domain_name, 
					self.adid,
					self.msg_type.value,
					','.join(self.finished), 
					','.join(self.running), 
					self.total_finished, 
					'%.2f' % float(self.speed) if self.speed is not None else 'NA'
				)
			else:
				return '[%s][%s][%s][%s]' % (self.type.value, self.domain_name, self.adid, self.msg_type.value)
		else:
			return '[%s][%s][%s][%s] PROGRESS %s/%s (%s) SPEED %s obj/s' % (
				self.type.value,
				self.domain_name, 
				self.adid,
				self.msg_type.value,
				self.total,
				self.total_finished,
				self.get_percentage(),
				'%.2f' % float(self.speed) if self.speed is not None else 'NA'
			)
		
