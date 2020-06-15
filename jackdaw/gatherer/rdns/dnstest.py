
from jackdaw.gatherer.rdns.rdns import RDNS


async def get_correct_dns_win(root_domain):
	"""
	root_domain must be a valid dns name
	"""
	from winacl.functions.winregistry import get_nameserver_candidates

	for dns_ip in get_nameserver_candidates():
		rdns = RDNS(dns_ip)
		res, err = await rdns.lookup(root_domain)
		if res is not None:
			return dns_ip
	
	return None
