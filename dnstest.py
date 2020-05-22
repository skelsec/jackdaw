import asyncio
from async_dns import types
from async_dns.resolver import ProxyResolver



async def rev_lookup(ip):
	resolver = ProxyResolver()
	res = await resolver.query(ip, types.PTR)
	print(res.__dict__)
	
	


asyncio.run(rev_lookup('194.143.245.39'))