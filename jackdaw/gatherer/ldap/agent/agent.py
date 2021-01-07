import traceback
import asyncio

from winacl.dtyp.security_descriptor import SECURITY_DESCRIPTOR

from jackdaw.dbmodel.utils.tokengroup import JackDawTokenGroup

from jackdaw.gatherer.ldap.agent.common import *
from jackdaw import logger
from jackdaw.dbmodel.spnservice import SPNService
from jackdaw.dbmodel.adgroup import Group
from jackdaw.dbmodel.adinfo import ADInfo
from jackdaw.dbmodel.aduser import ADUser
from jackdaw.dbmodel.adcomp import Machine
from jackdaw.dbmodel.adou import ADOU
from jackdaw.dbmodel.adinfo import ADInfo
from jackdaw.dbmodel.adgpo import GPO
from jackdaw.dbmodel.constrained import MachineConstrainedDelegation
from jackdaw.dbmodel.adgplink import Gplink
from jackdaw.dbmodel.adsd import JackDawSD
from jackdaw.dbmodel.adtrust import ADTrust
from jackdaw.dbmodel.adspn import JackDawSPN
from jackdaw.dbmodel import get_session
from jackdaw.dbmodel.edge import Edge
from jackdaw.dbmodel.edgelookup import EdgeLookup
from jackdaw.dbmodel.adallowedtoact import MachineAllowedToAct
from jackdaw.dbmodel.adschemaentry import ADSchemaEntry


class LDAPGathererAgent:
	def __init__(self, ldap_mgr, agent_in_q, agent_out_q):
		self.ldap_mgr = ldap_mgr
		self.agent_in_q = agent_in_q
		self.agent_out_q = agent_out_q
		self.ldap = None
		self.test_ctr = 0

	async def get_sds(self, data):
		try:
			#print(data)
			if data is None:
				await self.agent_out_q.put((LDAPAgentCommand.SDS_FINISHED, None))
				return

			dn = data['dn']
			
			adsec, err = await self.ldap.get_objectacl_by_dn(dn)
			if err is not None:
				raise err
			data['adsec'] = adsec
			await self.agent_out_q.put((LDAPAgentCommand.SD, data ))

		except:
			await self.agent_out_q.put((LDAPAgentCommand.EXCEPTION, str(traceback.format_exc())))

	async def get_all_effective_memberships(self):
		try:
			async for res, err in self.ldap.get_all_tokengroups():
				if err is not None:
					raise err
				s = JackDawTokenGroup()
				s.cn = res['cn']
				s.dn = res['dn']
				s.guid = res['guid']
				s.sid = res['sid']
				s.member_sid = res['token']
				s.objtype = res['type']
				await self.agent_out_q.put((LDAPAgentCommand.MEMBERSHIP, s))
		except:
			await self.agent_out_q.put((LDAPAgentCommand.EXCEPTION, str(traceback.format_exc())))
		finally:
			await self.agent_out_q.put((LDAPAgentCommand.MEMBERSHIPS_FINISHED, None))

	async def get_effective_memberships(self, data):
		try:
			if data is None:
				await self.agent_out_q.put((LDAPAgentCommand.MEMBERSHIPS_FINISHED, None))
				return
			async for res, err in self.ldap.get_tokengroups(data['dn']):
				if err is not None:
					raise err
				s = JackDawTokenGroup()
				s.guid = data['guid']
				s.sid = data['sid']
				s.member_sid = res
				s.object_type = data['object_type']
				await self.agent_out_q.put((LDAPAgentCommand.MEMBERSHIP, s))
		except:
			await self.agent_out_q.put((LDAPAgentCommand.EXCEPTION, str(traceback.format_exc())))
		finally:
			await self.agent_out_q.put((LDAPAgentCommand.MEMBERSHIP_FINISHED, None))
			

	async def get_all_trusts(self):
		try:
			async for entry, err in self.ldap.get_all_trusts():
				if err is not None:
					raise err
				await self.agent_out_q.put((LDAPAgentCommand.TRUSTS, ADTrust.from_ldapdict(entry.to_dict())))
		except:
			await self.agent_out_q.put((LDAPAgentCommand.EXCEPTION, str(traceback.format_exc())))
		finally:
			await self.agent_out_q.put((LDAPAgentCommand.TRUSTS_FINISHED, None))

	async def get_all_spnservices(self):
		try:
			async for entry, err in self.ldap.get_all_spn_entries():
				if err is not None:
					raise err
				if 'servicePrincipalName' not in entry['attributes']:
					continue
				
				for spn in entry['attributes']['servicePrincipalName']:
					port = None
					service_name = None
					service_class, t = spn.split('/',1)
					m = t.find(':')
					if m != -1:
						computername, port = t.rsplit(':',1)
						if port.find('/') != -1:
							port, service_name = port.rsplit('/',1)
					else:
						computername = t
						if computername.find('/') != -1:
							computername, service_name = computername.rsplit('/',1)

					s = SPNService()
					s.owner_sid = str(entry['attributes']['objectSid'])
					s.computername = computername
					s.service_class = service_class
					s.service_name = service_name
					if port is not None:
						s.port = str(port)
					await self.agent_out_q.put((LDAPAgentCommand.SPNSERVICE, s))
		except:
			await self.agent_out_q.put((LDAPAgentCommand.EXCEPTION, str(traceback.format_exc())))
		finally:
			await self.agent_out_q.put((LDAPAgentCommand.SPNSERVICES_FINISHED, None))

	async def get_all_users(self):
		try:
			async for user_data, err in self.ldap.get_all_users():
				if err is not None:
					raise err
				try:
					user = ADUser.from_aduser(user_data)
				except:
					await self.agent_out_q.put((LDAPAgentCommand.EXCEPTION, str(traceback.format_exc())))
					continue
				spns = []
				if user_data.servicePrincipalName is not None:
					for spn in user_data.servicePrincipalName:
						spns.append(JackDawSPN.from_spn_str(spn, user.objectSid))

				await self.agent_out_q.put((LDAPAgentCommand.USER, {'user':user, 'spns':spns}))
		except:
			await self.agent_out_q.put((LDAPAgentCommand.EXCEPTION, str(traceback.format_exc())))
		finally:
			await self.agent_out_q.put((LDAPAgentCommand.USERS_FINISHED, None))

	async def get_all_groups(self):
		try:
			async for group, err in self.ldap.get_all_groups():
				if err is not None:
					raise err
				g = Group.from_dict(group.to_dict())
				await self.agent_out_q.put((LDAPAgentCommand.GROUP, g))
				del g
		except:
			await self.agent_out_q.put((LDAPAgentCommand.EXCEPTION, str(traceback.format_exc())))
		finally:
			await self.agent_out_q.put((LDAPAgentCommand.GROUPS_FINISHED, None))

	async def get_all_schemaentries(self):
		try:
			async for se, err in self.ldap.get_all_schemaentry():
				if err is not None:
					raise err
				schemaentry = ADSchemaEntry.from_adschemaentry(se)
				await self.agent_out_q.put((LDAPAgentCommand.SCHEMA, schemaentry))
				del schemaentry
		except:
			await self.agent_out_q.put((LDAPAgentCommand.EXCEPTION, str(traceback.format_exc())))
		finally:
			await self.agent_out_q.put((LDAPAgentCommand.SCHEMA_FINISHED, None))
			

	async def get_all_gpos(self):
		try:
			async for gpo, err in self.ldap.get_all_gpos():
				if err is not None:
					raise err
				g = GPO.from_adgpo(gpo)
				await self.agent_out_q.put((LDAPAgentCommand.GPO, g))
				del g
		except:
			await self.agent_out_q.put((LDAPAgentCommand.EXCEPTION, str(traceback.format_exc())))
		finally:
			await self.agent_out_q.put((LDAPAgentCommand.GPOS_FINISHED, None))


	async def get_all_machines(self):
		try:
			async for machine_data, err in self.ldap.get_all_machines():
				if err is not None:
					raise err
				machine = Machine.from_adcomp(machine_data)
				
				delegations = []
				allowedtoact = []
				if machine_data.allowedtoactonbehalfofotheridentity is not None:
					try:
						sd = SECURITY_DESCRIPTOR.from_bytes(machine_data.allowedtoactonbehalfofotheridentity)
						if sd.Dacl is not None:
							for ace in sd.Dacl.aces:
								aa = MachineAllowedToAct()
								aa.machine_sid = machine.objectSid
								aa.target_sid = str(ace.Sid)
								allowedtoact.append(aa)
					except Exception as e:
						logger.debug('Error parsing allowedtoact SD! %s Reason: %s' % (machine.sAMAccountName, e))
				if machine_data.allowedtodelegateto is not None:
					for delegate_data in machine_data.allowedtodelegateto:
						delegations.append(MachineConstrainedDelegation.from_spn_str(delegate_data))
				await self.agent_out_q.put((LDAPAgentCommand.MACHINE, {'machine' : machine, 'delegations' : delegations, 'allowedtoact' : allowedtoact}))
		except:
			await self.agent_out_q.put((LDAPAgentCommand.EXCEPTION, str(traceback.format_exc())))
		finally:
			await self.agent_out_q.put((LDAPAgentCommand.MACHINES_FINISHED, None))

	async def get_all_ous(self):
		try:
			async for ou, err in self.ldap.get_all_ous():
				if err is not None:
					raise err
				o = ADOU.from_adou(ou)
				await self.agent_out_q.put((LDAPAgentCommand.OU, o))
				del o
		except:
			await self.agent_out_q.put((LDAPAgentCommand.EXCEPTION, str(traceback.format_exc())))
		finally:
			await self.agent_out_q.put((LDAPAgentCommand.OUS_FINISHED, None))

	async def get_domain_info(self):
		try:
			info, err = await self.ldap.get_ad_info()
			if err is not None:
				raise err
			adinfo = ADInfo.from_msldap(info)
			await self.agent_out_q.put((LDAPAgentCommand.DOMAININFO, adinfo))
		except:
			await self.agent_out_q.put((LDAPAgentCommand.EXCEPTION, str(traceback.format_exc())))
		finally:
			await self.agent_out_q.put((LDAPAgentCommand.DOMAININFO_FINISHED, None))

	async def setup(self):
		try:
			self.ldap = self.ldap_mgr.get_client()
			res, err = await self.ldap.connect()
			if err is not None:
				raise err
			return res
		except:
			await self.agent_out_q.put((LDAPAgentCommand.EXCEPTION, str(traceback.format_exc())))
			return False

	async def arun(self):
		try:
			res = await self.setup()
			if res is False:
				return
			while True:
				res = await self.agent_in_q.get()
				if res is None:
					return

				if res.command == LDAPAgentCommand.DOMAININFO:
					await self.get_domain_info()
				elif res.command == LDAPAgentCommand.USERS:
					await self.get_all_users()
				elif res.command == LDAPAgentCommand.MACHINES:
					await self.get_all_machines()
				elif res.command == LDAPAgentCommand.GROUPS:
					await self.get_all_groups()
				elif res.command == LDAPAgentCommand.OUS:
					await self.get_all_ous()
				elif res.command == LDAPAgentCommand.GPOS:
					await self.get_all_gpos()
				elif res.command == LDAPAgentCommand.SPNSERVICES:
					await self.get_all_spnservices()
				elif res.command == LDAPAgentCommand.SCHEMA:
					await self.get_all_schemaentries()
				#elif res.command == LDAPAgentCommand.MEMBERSHIPS:
				#	await self.get_all_effective_memberships()
				elif res.command == LDAPAgentCommand.MEMBERSHIPS:
					await self.get_effective_memberships(res.data)
				elif res.command == LDAPAgentCommand.SDS:
					await self.get_sds(res.data)
				elif res.command == LDAPAgentCommand.TRUSTS:
					await self.get_all_trusts()
		except Exception as e:
			logger.exception('Agent main!')
		finally:
			if self.ldap is not None:
				await self.ldap._con.disconnect()
			

	def run(self):
		try:
			loop = asyncio.get_event_loop()
		except:
			loop = asyncio.new_event_loop()
		#loop.set_debug(True)  # Enable debug
		loop.run_until_complete(self.arun())
