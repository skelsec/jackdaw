import asyncio

"""
This is a simple implementation, please use this only as a last-resort.
There are much better portscanners out there.
"""
class TCPPortScan:
	def __init__(self, ip, port, settings):
		self.ip = str(ip)
		self.port = port
		self.settings = settings

		if self.settings is None:
			self.settings = {}
			self.settings['timeout'] = 5

	
	async def run(self):
		try:
			reader, writer = await asyncio.wait_for(
				asyncio.open_connection(
					self.ip, 
					int(self.port),
				),
				timeout = self.settings['timeout']
			)
			writer.close()
			return True, None
		except ConnectionRefusedError:
			return True, ConnectionRefusedError
		except ConnectionResetError:
			return True, ConnectionResetError
		except Exception as e:
			return False, e