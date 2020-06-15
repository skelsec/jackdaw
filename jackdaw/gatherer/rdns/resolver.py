import asyncio
import socket
import ipaddress

from jackdaw.gatherer.rdns.protocol import DNSPacket, DNSQuestion, DNSResponse, DNSType, DNSClass, DNSFlags, DNSOpcode, DNSResponseCode
from jackdaw.gatherer.rdns.udpwrapper import UDPClient
import os

class Resolver:
	def __init__(self, server = '8.8.8.8', protocol = 'TCP', cache = True):
		self.server = server
		self.protocol = protocol
		self.cache = {}

	async def ptr(self, hostname):
		pass
	
	async def ptr(self, ip):
		try:
			if ip in self.cache:
				return self.cache[ip]
			ip = ipaddress.ip_address(ip).reverse_pointer
			tid = os.urandom(2)
			question = DNSQuestion.construct(ip, DNSType.PTR, DNSClass.IN, qu = False)
				
						
			if self.protocol == 'TCP':
				reader, writer = await asyncio.open_connection(self.server, 53)
		
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
				cli = UDPClient((self.server, 53))
				
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
			
			
async def amain(ip):
	resolver = RDNS(protocol = 'TCP')
	name, err = await resolver.resolve(ip)
	print(name)

if __name__ == '__main__':
	
	ip = '194.143.245.39'
	asyncio.run(amain(ip))