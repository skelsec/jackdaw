
import enum



class HASHCATCMDTYPE(enum.Enum):
	STOP = 'STOP'
	TASK = 'TASK'
	CRACKED = 'CRACKED'
	STATUS = 'STATUS'

class HashcatTask:
	def __init__(self):
		self.type = HASHCATCMDTYPE.TASK
		self.hashtype = None
		self.hashes = []
		self.mode = None
		self.mask = None
		self.wordlists = []
		self.rulefile = None
		self.status_interval = 10

class HashcatStop:
	def __init__(self):
		self.type = HASHCATCMDTYPE.STOP

class HashcatCracked:
	def __init__(self):
		self.type = HASHCATCMDTYPE.CRACKED
		self.crackdict = {} #hash:plaintext

class HashcatStatus:
	def __init__(self):
		self.type = HASHCATCMDTYPE.STATUS
		self.speed:int = None #cracking speed
		self.progress:int = None #percentage 
		self.recovered:int = None # (cracked/total hashes)
		self.total:int = None #total hashes submitted



#### ===================== MANAGER ==============================

class HashcatMgrTaskStop:
	def __init__(self):
		self.token = None
		self.type = HASHCATCMDTYPE.STOP

class HashcatMgrTaskStatus:
	def __init__(self):
		self.token = None
		self.type = HASHCATCMDTYPE.STATUS

class HashcatMgrTaskStatus:
	def __init__(self):
		self.token = None
		self.type = HASHCATCMDTYPE.STATUS

class HashcatMgrTask:
	def __init__(self):
		self.token = None
		self.type = HASHCATCMDTYPE.TASK
		self.hashtype = None
		self.hashes = []
		self.mode = None
		self.mask = None
		self.wordlists = []
		self.rulefile = None
		self.status_interval = 10