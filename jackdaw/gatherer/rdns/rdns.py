import asyncio
import socket
import ipaddress
import traceback
from typing import List

from asysocks.common.clienturl import SocksClientURL
from asysocks.common.comms import SocksQueueComms
from asysocks.client import SOCKSClient
from jackdaw.gatherer.rdns.protocol import DNSPacket, DNSQuestion, DNSResponse, DNSType, DNSClass, DNSFlags, DNSOpcode, DNSResponseCode
from jackdaw.gatherer.rdns.udpwrapper import UDPClient
import os

class DNSTarget:
	def __init__(self, ip, port = 53, protocol = 'TCP', timeout = 5, proxy = None):
		self.ip = ip
		self.port = port
		self.protocol = protocol
		self.timeout = timeout
		self.proxy = proxy

class RDNS:
	def __init__(self, target:DNSTarget, cache:bool = True):
		self.target = target
		self.cache_enabled = cache
		self.cache = {}

		self.proxyobj = None
		self.proxy_task = None
		self.in_q = None
		self.out_q = None

	async def setup(self):
		try:
			if self.target.proxy is None:
				# no need for additional setup
				return None, None
			
			self.in_q = asyncio.Queue()
			self.out_q = asyncio.Queue()
			comms = SocksQueueComms(self.in_q, self.out_q)
			self.proxyobj = SOCKSClient(comms, self.target.proxy)
			self.proxy_task = asyncio.create_task(self.proxyobj.run())
			return None, None
		except Exception as e:
			return None, e



	async def lookup(self, hostname, dnstype = DNSType.A):
		_, err = await self.setup()
		if err is not None:
			return None, err
		try:
			question = DNSQuestion.construct(str(hostname), dnstype, DNSClass.IN, qu = False)
			if self.proxyobj is None:
				if self.target.protocol == 'TCP':
					reader, writer = await asyncio.wait_for(asyncio.open_connection(self.target.ip, self.target.port), self.target.timeout)
			
					packet = DNSPacket.construct(
						TID = os.urandom(2), 
						flags = DNSFlags.RD,
						response = DNSResponse.REQUEST, 
						opcode = DNSOpcode.QUERY, 
						rcode = DNSResponseCode.NOERR, 
						questions= [question], 
						proto = socket.SOCK_STREAM
					)
					
					writer.write(packet.to_bytes())
					await writer.drain()
					
					data = await DNSPacket.from_streamreader(reader, proto = socket.SOCK_STREAM)
					writer.close()
					return data.Answers[0].ipaddress, None
				else:
					raise NotImplementedError()
			else:
				if self.target.protocol == 'TCP':
					packet = DNSPacket.construct(
						TID = os.urandom(2), 
						flags = DNSFlags.RD,
						response = DNSResponse.REQUEST, 
						opcode = DNSOpcode.QUERY, 
						rcode = DNSResponseCode.NOERR, 
						questions= [question], 
						proto = socket.SOCK_STREAM
					)

					await self.in_q.put(packet.to_bytes())
					x = await DNSPacket.from_queue(self.out_q, b'', proto = socket.SOCK_STREAM)
					packet, rem = x
					if len(packet.Answers) == 0:
						raise Exception("No answer found in packet")
					return packet.Answers[0].ipaddress, None
				
				else:
					raise NotImplementedError()


		except Exception as e:
			return None, e
		finally:
			if self.proxyobj is not None:
				await self.proxyobj.terminate()


	async def resolve(self, ip):
		try:
			if self.cache_enabled is True and ip in self.cache:
				return self.cache[ip]
			ip = ipaddress.ip_address(ip).reverse_pointer
			tid = os.urandom(2)
			question = DNSQuestion.construct(ip, DNSType.PTR, DNSClass.IN, qu = False)
				
						
			if self.target.protocol == 'TCP':
				reader, writer = await asyncio.wait_for(asyncio.open_connection(self.target.ip, self.target.port), self.target.timeout)
		
				packet = DNSPacket.construct(
					TID = tid,
					flags = DNSFlags.RD,
					response = DNSResponse.REQUEST,
					opcode = DNSOpcode.QUERY,
					rcode = DNSResponseCode.NOERR,
					questions= [question],
					proto = socket.SOCK_STREAM
				)
				
				writer.write(packet.to_bytes())
				await writer.drain()
				
				data = await DNSPacket.from_streamreader(reader, proto = socket.SOCK_STREAM)
				self.cache[ip] = data.Answers[0].domainname
				writer.close()
				return data.Answers[0].domainname, None
			else:
				cli = UDPClient((self.target.server, self.target.port))
				
				packet = DNSPacket.construct(
					TID = tid, 
					flags = DNSFlags.RD,
					response = DNSResponse.REQUEST,
					opcode = DNSOpcode.QUERY,
					rcode = DNSResponseCode.NOERR,
					questions= [question],
					proto = socket.SOCK_DGRAM
				)
						
				reader, writer = await cli.run(packet.to_bytes())
				data = await DNSPacket.from_streamreader(reader)
				self.cache[ip] = data.Answers[0].domainname
				return data.Answers[0].domainname, None
		
		except Exception as e:
			return None, e
		finally:
			if self.proxyobj is not None:
				await self.proxyobj.terminate()

async def amain_lookup(hostname):
	resolver = RDNS(protocol = 'TCP')
	name, err = await resolver.lookup(hostname, dnstype = DNSType.AAAA)
	print(name)
	print(err)
			
async def amain(ip):
	resolver = RDNS(protocol = 'TCP')
	name, err = await resolver.resolve(ip)
	print(name)

if __name__ == '__main__':
	hostname = 'google.com'
	asyncio.run(amain_lookup(hostname))
	#ip = '194.143.245.39'
	#asyncio.run(amain(ip))