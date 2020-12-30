
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

		self.video_width = 1024
		self.video_height = 768
		self.video_dpi = 92

		self.audio_format = 'audio/ogg'
		self.image_format = 'image/png'


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
		
		print(serialize(data))
		self.writer.write(serialize(data))
		await self.writer.drain()

	async def handshake(self, protocol, connect_params):
		try:
			# the keys/values in connect_params depends on the protocol

			# handshake init with the specified destination protocol
			handshake_init = ('6.select,%s.%s;' % (len(protocol), protocol) ).encode()
			self.writer.write(handshake_init)
			await self.writer.drain()
			handshake_res = await self.recv_data()
			
			# handshake_res will contain the list of argument names we will need to reply to

			# this section is sent befor the connect message, and is mandatory for some reason
			size_data  = '4.size,%s.%s,%s.%s,%s.%s;' % ( len(str(self.video_height)), str(self.video_height), len(str(self.video_width)), str(self.video_width) , len(str(self.video_dpi)), str(self.video_dpi) )
			audio_data = '5.audio,%s.%s;' % (len(str(self.audio_format)), str(self.audio_format))
			video_data = '5.video;' #currently no video supported
			image_data = '5.image,%s.%s;' % (len(str(self.image_format)), str(self.image_format))
			handshake_reply = (size_data + audio_data + video_data + image_data).encode('ascii')
			
			# constructing the connect message
			pt = [b'7.connect', b'13.VERSION_1_1_0']
			for key in handshake_res[2:]:
				if key not in connect_params or connect_params[key] is None:
					pt.append(b'0.')
					continue
				pt.append(('%s.%s' % (len(connect_params[key]), connect_params[key])).encode())
			
			handshake_reply += b','.join(pt) + b';'
			#print('%s' % handshake_reply)
			self.writer.write(handshake_reply)
			await self.writer.drain()

			# the connect message's result is a token
			res = await self.recv_data()
			#print(res)
			token = res[1] #.replace('$','')
			#print(token)
			return token

		except Exception as e:
			traceback.print_exc()

	async def connect_rdp(self, hostname = None, port = 3389, domain = None, username = None, password = None):
		try:
			self.reader, self.writer = await asyncio.open_connection(self.guac_ip, self.guac_port)
			connect_params = {
				'hostname' : hostname,
				'port' : str(port),
				'domain' : domain,
				'username' : username,
				'password': password,
				'width' : str(self.video_width),
				'height' : str(self.video_height),
				'dpi' : str(self.video_dpi),
				'timezone' : 'America/New_York',
				'ignore-cert' : 'true',
			}
			token = await self.handshake('rdp', connect_params)
			#print(token)	
			token_cmd = '0.,%s.%s;' % (len(token), token)
			#print(token_cmd)
			await self.ws.send(token_cmd)

			#print('PROXY')

			asyncio.create_task(self.__proxy_incoming())
			asyncio.create_task(self.__proxy_outgoing())
			await self.proxy_stop_evt.wait()
		
			#print('DONE')
		except Exception as e:
			print('XXXX')
			traceback.print_exc()

	async def connect_vnc(self, hostname = None, port = 5900, domain = None, username = None, password = None):
		try:
			self.reader, self.writer = await asyncio.open_connection(self.guac_ip, self.guac_port)
			connect_params = {
				'hostname' : hostname,
				'port' : str(port),
				'domain' : domain,
				'username' : username,
				'password': password,
				'width' : str(self.video_width),
				'height' : str(self.video_height),
				'dpi' : str(self.video_dpi),
				'timezone' : 'America/New_York',
				'ignore-cert' : 'true',
			}
			token = await self.handshake('vnc', connect_params)			
			token_cmd = '0.,%s.%s;' % (len(token), token)
			#print(token_cmd)
			await self.ws.send(token_cmd)

			#print('PROXY')

			asyncio.create_task(self.__proxy_incoming())
			asyncio.create_task(self.__proxy_outgoing())
			await self.proxy_stop_evt.wait()
		
			#print('DONE')
		except Exception as e:
			print('XXXX')
			traceback.print_exc()

	async def connect_ssh(self, hostname = None, port = 22, domain = None, username = None, password = None):
		try:
			self.reader, self.writer = await asyncio.open_connection(self.guac_ip, self.guac_port)
			connect_params = {
				'hostname' : hostname,
				'port' : str(port),
				'domain' : domain,
				'username' : username,
				'password': password,
				'width' : str(self.video_width),
				'height' : str(self.video_height),
				'dpi' : str(self.video_dpi),
				'timezone' : 'America/New_York',
				'ignore-cert' : 'true',
			}
			token = await self.handshake('ssh', connect_params)			
			token_cmd = '0.,%s.%s;' % (len(token), token)
			#print(token_cmd)
			await self.ws.send(token_cmd)

			#print('PROXY')

			asyncio.create_task(self.__proxy_incoming())
			asyncio.create_task(self.__proxy_outgoing())
			await self.proxy_stop_evt.wait()
		
			#print('DONE')
		except Exception as e:
			print('XXXX')
			traceback.print_exc()