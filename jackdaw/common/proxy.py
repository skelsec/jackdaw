import enum
from urllib.parse import urlparse, parse_qs

class ProxyType(enum.Enum):
	SOCKS5 = 'SOCKS5'
	SOCKS5_SSL = 'SOCKS5_SSL'
	MULTIPLEXOR = 'MULTIPLEXOR'
	MULTIPLEXOR_SSL = 'MULTIPLEXOR_SSL'

class ProxyConnection:
	"""
	socks5://127.0.0.1:5555
	socks5://user:password@127.0.0.1:5555
	socks5-ssl://127.0.0.1:4444
	socks5-ssl://user:password@127.0.0.1:5555
	multiplexor://127.0.0.1:5555/agentid
	multiplexor://user:password@127.0.0.1:5555/agentid
	multiplexor-ssl://127.0.0.1:5555/agentid
	multiplexor-ssl://user:password@127.0.0.1:5555/agentid
	"""
	def __init__(self):
		self.ip = None
		self.port = None
		self.username = None
		self.domain = None
		self.password = None
		self.timeout = None
		self.type = None
		self.dns = None

	@staticmethod
	def from_connection_string(s):
		url_e = urlparse(s)
		pt = ProxyType(url_e.scheme.replace('-', '_').upper())
		if pt in [ProxyType.SOCKS5, ProxyType.SOCKS5_SSL]:
			pc = Socks5ProxyConnection()
		elif pt in [ProxyType.MULTIPLEXOR, ProxyType.MULTIPLEXOR_SSL]:
			pc = MultiplexorProxyConnection()
		
		pc.type = pt
		pc.ip = url_e.hostname
		pc.port = url_e.port

		if url_e.username is not None:
			if url_e.username.find('\\') != -1:
				pc.domain, pc.username = url_e.username.split('\\')
			else:
				pc.username = url_e.username
			pc.password = url_e.password

		params = parse_qs(url_e.params)
		if 'timeout' in params:
			pc.timeout = int(params['timeout'][0])
		if 'dns' in params:
			pc.dns = params['dns']
		
		pc.parse_rest(url_e)
		return pc

	def __str__(self):
		t = '==== ProxyConnection ====\r\n'
		for k in self.__dict__:
			t += '%s: %s\r\n' % (k, self.__dict__[k])
			
		return t


class Socks5ProxyConnection(ProxyConnection):
	def __init__(self):
		ProxyConnection.__init__(self)

	def parse_rest(self, url_e):
		return

	def get_ldap(self):
		pass

	def get_smb(self):
		pass


class MultiplexorProxyConnection(ProxyConnection):
	def __init__(self):
		ProxyConnection.__init__(self)
		self.agentid = None

	def parse_rest(self, url_e):
		self.agentid = url_e.path.replace('/','')
		if self.agentid is None:
			raise Exception('Multiplexor proxy requires agentid to be set!')
		return

	def get_ldap(self):
		pass

	def get_smb(self):
		pass


if __name__ == '__main__':
	url_tests = [
		'socks5://127.0.0.1:5555',
		'socks5://user:password@127.0.0.1:5555',
		'socks5://aaa\\user:password@127.0.0.1:5555',
		'socks5-ssl://127.0.0.1:4444',
		'socks5-ssl://user:password@127.0.0.1:5555',
		'multiplexor://127.0.0.1:5555/agentid',
		'multiplexor://user:password@127.0.0.1:5555/agentid',
		'multiplexor-ssl://127.0.0.1:5555/agentid',
		'multiplexor-ssl://user:password@127.0.0.1:5555/agentid',
		'multiplexor-ssl://aaa\\user:password@127.0.0.1:5555/agentid',
		'multiplexor-ssl://aaa\\user:password@127.0.0.1:5555/agentid?user=alma&domain=test&password=44444',

	]
	for url in url_tests:
		print('===========================================================================')
		print(url)
		try:
			dec = ProxyConnection.from_connection_string(url)
		except Exception as e:
			import traceback
			traceback.print_exc()
			print('ERROR! Reason: %s' % e)
			input()
		else:
			print(str(dec))
			#print(str(target))
			input()