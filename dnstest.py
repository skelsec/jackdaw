import asyncdns, asyncio
from aiodnsresolver import Resolver, TYPES




async def rev_lookup(ip):
	resolve, _ = Resolver()
	ip_addresses = await resolve(ip, TYPES.PTR)
	print(ip_addresses)

asyncio.run(rev_lookup('8.8.8.8'))