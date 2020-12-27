
import traceback
import asyncio


def encode_lv(data):
	if data is None:
		return b'0.'
	return ('%s.%s' % (len(data), data)).encode('ascii')

def decode_lv(data):
	length, value = data.split('.',1)
	if(len(value) != int(length)):
		raise Exception('Incorrect length! %s' % data)
	return value

def serialize(cmd):
	buff = b','.join(encode_lv(cmd[k]) for k in cmd) + b';'
	return buff

def deserialize(data):
	if isinstance(data, bytes):
		data = data.decode('ascii')
	data = data[:-1]
	return [decode_lv(element) for element in data.split(',')]

class GuacProxy:
	def __init__(self, guac_ip, guac_port, ws):
		self.guac_ip = guac_ip
		self.guac_port = guac_port
		self.ws = ws
		self.proxy_stop_evt = asyncio.Event()

		self.reader = None
		self.writer = None

	async def __proxy_incoming(self):
		try:
			while not self.proxy_stop_evt.is_set():
				await asyncio.sleep(0)
				data = await self.reader.readuntil(b';')
				if data == b'':
					print('EMPTY!')
					break
				#print('incoming %s' % data)
				await self.ws.send(data.decode())
		except Exception as e:
			traceback.print_exc()
		
		finally:
			self.proxy_stop_evt.set()

	async def __proxy_outgoing(self):
		try:
			while not self.proxy_stop_evt.is_set():
				await asyncio.sleep(0)
				data = await self.ws.recv()
				#print('outgoing %s' % data)
				self.writer.write(data.encode())
				await self.writer.drain()
		except Exception as e:
			self.proxy_stop_evt.set()
			traceback.print_exc()

	async def recv_data(self):
		data = await self.reader.readuntil(b';')
		res = deserialize(data)
		return res

	async def send_data(self, data):
		if not isinstance(data, dict):
			data = data.to_dict()
		self.writer.write(serialize(data))
		await self.writer.drain()

	async def connect_rdp(self, hostname = None, domain = None, username = None, password = None):
		try:
			self.reader, self.writer = await asyncio.open_connection(self.guac_ip, self.guac_port)
			dd = {
				'ins': 'select',
				'protocol' : "rdp",
			}
			await self.send_data(dd)
			await self.recv_data()
			
			
			dd = {
				'ins': 'size',
				'height' : "1024",
				'width' : "768",
				'dpi' : "96",
			}
			await self.send_data(dd)

			dd = {
				'ins' : 'audio',
				'format' : 'audio/ogg'
			}
			await self.send_data(dd)

			dd = {
				'ins' : 'video', #not supported
			}
			await self.send_data(dd)

			dd = {
				'ins' : 'image',
				'type1' : 'image/png',
				'type2' : 'image/jpeg',
			}
			await self.send_data(dd)

			dd = {
				'ins' : 'timezone',
				'timezone' : 'America/New_York'
			}
			await self.send_data(dd)

			dd = {
				'ins' : 'connect',
				'version' : 'VERSION_1_1_0',
				'hostname' : hostname,
				'port' : "3389",
				'domain' : domain,
				'user' : username,
				'password' : password,
			}
			for i in range(18):
				dd[str(i)] = None
			dd[str(18)] = 'true'
			for i in range(19, 71, 1):
				dd[str(i)] = None
			await self.send_data(dd)

			res = await self.recv_data()
			print(res)
			token = res[1].replace('$','')
			print(token)
			data = '0.,%s.%s;' % (len(token), token)
			print(token)
			print(2)
			await self.ws.send(data)

			print('PROXY')

			asyncio.create_task(self.__proxy_incoming())
			asyncio.create_task(self.__proxy_outgoing())
			await self.proxy_stop_evt.wait()
		
			print('DONE')
		except Exception as e:
			print('XXXX')
			traceback.print_exc()