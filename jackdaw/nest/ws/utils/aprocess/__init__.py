import enum
import sys

class PROCMSGTYPE(enum.Enum):
	KILL = 'KILL'
	STOPPED = 'STOPPED'
	MSG = 'MSG'
	MSGLIST = 'MSGLIST'

class PROCMSGSRC(enum.Enum):
	STDOUT = 'STDOUT'
	STDERR = 'STDERR'
	
class PROCKILL:
	def __init__(self):
		self.type:PROCMSGTYPE = PROCMSGTYPE.KILL

class PROCMSG:
	def __init__(self, data:bytes = None, datatxt:str = None, src:PROCMSGSRC = None, txtencodeing:str = sys.stdout.encoding):
		self.type:PROCMSGTYPE = PROCMSGTYPE.MSG
		self.data:bytes = data
		self.datatxt:str = datatxt
		self.txtencodeing:str = txtencodeing
		self.src:PROCMSGSRC = src
	
	def get_txt(self, encoding = sys.stdout.encoding):
		if self.datatxt is None:
			return self.data.decode(encoding)
		return self.datatxt
	
	def get_data(self, encoding = sys.stdout.encoding):
		if self.data is None:
			return self.datatxt.encode(encoding)
		return self.data

class PROCMSGLIST:
	def __init__(self):
		self.type:PROCMSGTYPE = PROCMSGTYPE.MSGLIST
		self.msgs = []


class PROCSTOPPED:
	def __init__(self, errno = None):
		self.type:PROCMSGTYPE = PROCMSGTYPE.STOPPED
		self.errno:int = errno