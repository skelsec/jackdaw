import asyncio
import json
import traceback
import pprint

import aiohttp


class ACLPwn:
	def __init__(self, url, ldap_url, smb_url, graph_id, start_user_sid = None):
		self.jd_url = url
		self.ldap_url = ldap_url
		self.smb_url = smb_url
		self.graph_id = graph_id
		self.start_user_sid = start_user_sid
		self.domainsids = []
		self.dagroups = []

		self.is_graph_loaded = False

	async def load_graph(self):
		try:
			print('Asking server to load graph data to memory...')
			async with aiohttp.ClientSession() as session:
				async with session.post('%s/graph?adids=%s' % (self.jd_url, self.graph_id)) as resp:
					if resp.status != 200:
						raise Exception('Loading graphid failed! Status: %s' % resp.status)
					await resp.text()

			self.is_graph_loaded = True
			return True, None
		except Exception as e:
			return False, e
	
	async def get_path_owned_da(self):
		try:
			async with aiohttp.ClientSession() as session:
				async with session.get('%s/graph?adids=%s' % (self.jd_url,self.graph_id)) as resp:
					if resp.status != 200:
						raise Exception('get_path_owned_dafailed! Status: %s' % resp.status)
					await resp.text()

		except Exception as e:
			return False, e

		
	async def get_path(self, src_sid, dst_sid, exclude = ['hasSession']):
		try:
			url = '%s/graph/%s/query/path?src=%s&dst=%s&format=%s' % (self.jd_url,self.graph_id, src_sid, dst_sid, 'path')
			if len(exclude) > 0:
				exclude = '%2C'.join(exclude)
			url += '&exclude=%s' % exclude
			print(url)
			async with aiohttp.ClientSession() as session:
				async with session.get(url) as resp:
					print(resp.status)
					if resp.status != 200:
						raise Exception('Loading graphid failed! Status: %s' % resp.status)
					data = await resp.text()
			print(data)
			res = json.loads(data)
			pprint.pprint(res)
			return res, None
		except Exception as e:
			return False, e
	
	async def get_domainsids(self):
		try:
			async with aiohttp.ClientSession() as session:
				async with session.get('%s/graph/%s/getdomainsids/' % (self.jd_url,self.graph_id)) as resp:
					print(resp.status)
					if resp.status != 200:
						raise Exception('Loading graphid failed! Status: %s' % resp.status)
					body = await resp.text()
					print(body)
					self.domainsids = json.loads(body)
			
			for dsid in self.domainsids:
				if dsid.endswith('-') is False:
					dsid += '-'
				self.dagroups.append(dsid+'512')

			return True, None
		except Exception as e:
			return False, e
	
	async def changepw_user(self):
		#password reset
		pass
	
	async def genericall_user(self):
		#password reset
		pass

	async def genericall_group(self):
		#add user to group
		pass
	
	#genericall/genericwrite/write on computer: resource based constrained

	async def writeproperty_group(self):
		#add user to group
		pass

	async def self_group(self):
		#add user to group
		pass
	
	async def writeowner_group(self):
		#change the owner of the group to the given user
		pass

	async def genericwrite_user(self):
		# can change some attributes, scriptpath attr will load a script on next logon to the user
		pass

	async def add_dcsync(self, user_dn):
		#assigns dcsync rights to the given user
		pass

	async def build_chain(self, paths):
		try:
			print('build_chain')
			print()
			paths = sorted(paths, key=len) #favouring shorter paths
			for path in paths:
				curr_user = path[0]
				print(curr_user)
				i = 1
				while i < len(path)-1:
					if path[i] == 'member':
						i += 2
						continue
					else:
						print('label: %s' % path[i])
						i += 1

			
			return True, None
		except Exception as e:
			return False, e

	async def run(self):
		try:
			if self.is_graph_loaded is False:
				_, err = await self.load_graph()
				if err is not None:
					raise err
			
			if len(self.domainsids) == 0:
				_, err = await self.get_domainsids()
				if err is not None:
					raise err
			
			if self.start_user_sid is not None:
				paths = []
				for dasid in self.dagroups:
					res, err = await self.get_path(self.start_user_sid, dasid)
					if err is not None:
						raise err
					paths += res


			else:
				paths, err = await self.get_path_owned_da()
				if err is not None:
					raise err
				
			chain, err = await self.build_chain(paths)
			if err is not None:
				raise err
			


			return True, None
		except Exception as e:
			traceback.print_exc()
			return False, e


def main():
	import argparse

	parser = argparse.ArgumentParser(description='acl autopwn')
	parser.add_argument('url', default='http://127.0.0.1:5000', help = 'server listen ip')
	parser.add_argument('ldapurl', help = 'server listen port')
	parser.add_argument('smburl', help = 'server listen ip')
	parser.add_argument('graphid', default = 1, type=int, help = 'graphid')
	parser.add_argument('-u', '--user-sid', help = 'Start user SID')

	args = parser.parse_args()

	ap = ACLPwn(args.url, args.ldapurl, args.smburl, args.graphid, args.user_sid)

	asyncio.run(ap.run())

if __name__ == '__main__':
	main()