import asyncio
import traceback
import shlex

import websockets

from jackdaw.external.aiocmd.aiocmd import aiocmd
from jackdaw import logger

from jackdaw.nest.ws.protocol import *


class NestWebScoketClientConsole(aiocmd.PromptToolkitCmd):
	def __init__(self, url):
		aiocmd.PromptToolkitCmd.__init__(self, ignore_sigint=False) #Setting this to false, since True doesnt work on windows...
		self.url = url
		self.reply_dispatch_table = {} # token -> queue
		self.token_ctr = 1 #start at 1, because 0 is reserved for server notifications
		self.ad_id = None
		self.handle_in_task = None
		self.websocket = None
		self.creds = {} #credid -> customcred
		self.targets = {}
		self.current_agent = "0"


	async def __handle_in(self):
		while True:
			try:
				data = await self.websocket.recv()
				#print('DATA IN -> %s' % data)
				cmd = NestOpCmdDeserializer.from_json(data)
				if cmd.cmd == NestOpCmd.LOG:
					print('LOG!')
					continue
				if cmd.token not in self.reply_dispatch_table:
					print('Unknown reply arrived! %s' % cmd)
					continue
				
				await self.reply_dispatch_table[cmd.token].put(cmd)

			except Exception as e:
				traceback.print_exc()
				#print('Reciever error %s' % e)
				return

	def __get_token(self):
		t = self.token_ctr
		self.token_ctr += 1
		return t

	async def __send_cmd(self, cmd):
		"sends the command and returns the token to identify the response if needed"
		cmd.token = self.__get_token()
		await self.websocket.send(cmd.to_json())
		return cmd.token

	async def __sr(self, cmd):
		"""send and recieve, use this when the command has an expected return value"""
		"""It also ssigns toke n to the cmd!"""
		try:
			msg_queue = asyncio.Queue()
			cmd.token = self.__get_token()
			print('Sending : %s' % cmd.to_json())
			self.reply_dispatch_table[cmd.token] = msg_queue
			await self.websocket.send(cmd.to_json())
			return msg_queue, None

		except Exception as e:
			return None, e

	async def do_connect(self):
		"""Performs connection"""
		try:			
			self.websocket = await websockets.connect(self.url)
			self.handle_in_task = asyncio.create_task(self.__handle_in())
			await asyncio.sleep(0)
			await self.do_listcreds(False)
			await self.do_listtargets(False)
			return True, None
		except Exception as e:
			traceback.print_exc()
			return False, e
	
	async def do_addcred(self, domain, username, stype, secret):
		"""Adds a new credential to the database"""
		try:			
			cmd = NestOpAddCred()
			cmd.username = username
			cmd.domain = domain
			cmd.stype = stype
			cmd.secret = secret
			cmd.description = None
			outq, err = await self.__sr(cmd)
			if err is not None:
				raise err
			while True:
				msg = await outq.get()
				if msg.cmd == NestOpCmd.OK:
					break
				elif msg.cmd == NestOpCmd.ERR:
					raise Exception(msg.reason)
				elif msg.cmd == NestOpCmd.CREDRES:
					self.creds[msg.cid] = msg
				
			await self.do_listcreds()
			return True, None
		except Exception as e:
			traceback.print_exc()
			return False, e
	
	async def do_listcreds(self, to_print = True):
		"""Refereshes the list of available credentials from the server"""
		try:
			self.creds = {}
			cmd = NestOpListCred()
			outq, err = await self.__sr(cmd)
			if err is not None:
				raise err
			while True:
				msg = await outq.get()
				if msg.cmd == NestOpCmd.OK:
					break
				elif msg.cmd == NestOpCmd.ERR:
					raise Exception(msg.reason)
				elif msg.cmd == NestOpCmd.CREDRES:
					self.creds[msg.cid] = msg
			
			if to_print is True:
				await self.do_creds()
			return True, None
		except Exception as e:
			traceback.print_exc()
			return False, e
	
	async def do_addtarget(self, hostname_or_ip):
		"""Adds a new target to the database"""
		try:			
			cmd = NestOpAddTarget()
			cmd.hostname = hostname_or_ip
			outq, err = await self.__sr(cmd)
			if err is not None:
				raise err
			while True:
				msg = await outq.get()
				if msg.cmd == NestOpCmd.OK:
					break
				elif msg.cmd == NestOpCmd.ERR:
					raise Exception(msg.reason)
				elif msg.cmd == NestOpCmd.TARGETRES:
					self.targets[msg.tid] = cmd
				
			await self.do_listtargets()
			return True, None
		except Exception as e:
			traceback.print_exc()
			return False, e
	
	async def do_listtargets(self, to_print = True):
		"""Refereshes the list of available targets from the server"""
		try:			
			cmd = NestOpListTarget()
			outq, err = await self.__sr(cmd)
			if err is not None:
				raise err
			while True:
				msg = await outq.get()
				if msg.cmd == NestOpCmd.OK:
					break
				elif msg.cmd == NestOpCmd.ERR:
					raise Exception(msg.reason)
				elif msg.cmd == NestOpCmd.TARGETRES:
					self.targets[msg.tid] = msg
			
			if to_print is True:
				await self.do_targets()
			return True, None
		except Exception as e:
			traceback.print_exc()
			return False, e
	
	async def do_targets(self):
		"""Prints currently available targets"""
		try:				
			for tid in self.targets:
				print('%s: %s' % (tid, self.targets[tid].hostname))
			return True, None
		except Exception as e:
			traceback.print_exc()
			return False, e
	
	async def do_creds(self):
		"""Prints currently available credentials"""
		try:
			for cid in self.creds:
				print('%s: %s' % (cid, self.creds[cid].to_credline()))
			return True, None
		except Exception as e:
			traceback.print_exc()
			return False, e
	
	async def do_getobj(self, oid):
		"""Fetches a user/machine/group etc... object from the server"""
		try:			
			cmd = NestOpGetOBJInfo()
			cmd.oid = oid
			outq, err = await self.__sr(cmd)
			if err is not None:
				raise err
			while True:
				msg = await outq.get()
				if msg.cmd == NestOpCmd.OK:
					break
				elif msg.cmd == NestOpCmd.ERR:
					raise Exception(msg.reason)
				else:
					print(msg)
			
			return True, None
		except Exception as e:
			traceback.print_exc()
			return False, e

	async def do_listads(self):
		"""Lists available ADs"""
		try:			
			cmd = NestOpListAD()
			outq, err = await self.__sr(cmd)
			if err is not None:
				raise err

			while True:
				msg = await outq.get()
				if msg.cmd == NestOpCmd.OK:
					break
				elif msg.cmd == NestOpCmd.ERR:
					raise Exception(msg.reason)
				elif msg.cmd == NestOpCmd.LISTADSRES:
					print('Available AD_ID: %s' % msg.adids)
			
			return True, None
		except Exception as e:
			traceback.print_exc()
			return False, e
	
	async def do_listgraphs(self):
		"""List graphs"""
		try:			
			cmd = NestOpListGraph()
			outq, err = await self.__sr(cmd)
			if err is not None:
				raise err
			while True:
				msg = await outq.get()
				if msg.cmd == NestOpCmd.OK:
					break
				elif msg.cmd == NestOpCmd.ERR:
					raise Exception(msg.reason)
				elif msg.cmd == NestOpCmd.LISTGRAPHRES:
					print('GRAPH: %s' % msg.gids)
			return True, None
		except Exception as e:
			traceback.print_exc()
			return False, e

	async def do_pathda(self):
		"""Calculates all paths to DA"""
		try:			
			cmd = NestOpPathDA()
			msg_queue, err = await self.__sr(cmd)
			if err is not None:
				raise err

			while True:
				msg = await msg_queue.get()
				if msg.cmd == NestOpCmd.OK:
					break
				elif msg.cmd == NestOpCmd.ERR:
					raise Exception(msg.reason)
				elif msg.cmd == NestOpCmd.PATHRES:
					print('PATH in: %s' % msg)

			return True, None
		except Exception as e:
			traceback.print_exc()
			return False, e

	async def do_listagents(self):
		"""List available agents"""
		try:			
			cmd = NestOpListAgents()
			msg_queue, err = await self.__sr(cmd)
			if err is not None:
				raise err
			while True:
				msg = await msg_queue.get()
				if msg.cmd == NestOpCmd.OK:
					break
				elif msg.cmd == NestOpCmd.ERR:
					raise Exception(msg.reason)
				elif msg.cmd == NestOpCmd.AGENT:
					print('AGENT: %s' % msg.agentid)
					self.current_agent = msg.agentid

			return True, None
		except Exception as e:
			traceback.print_exc()
			return False, e

	async def do_changegraph(self, graphid):
		"""Change current graph"""
		try:
			
			cmd = NestOpChangeGraph()
			cmd.graphid = graphid
			print(cmd.to_dict())
			data, err = await self.__sr(cmd)
			if err is not None:
				print('Failed to get data. Reason: %s' % err)
				return False, err
			print(data)
			return True, None
		except Exception as e:
			traceback.print_exc()
			return False, e

	async def do_gather(self, ldap_credid, ldap_targetid, smb_credid, smb_targetid, kerberos_credid = None, kerberos_targetid = None, dns_target = None, agentid = None):
		"""Perform full gather on an agent"""
		try:
			cmd = NestOpGather()
			cmd.agent_id = agentid
			if agentid is None:
				cmd.agent_id = self.current_agent
			
			cmd.ldap_creds, stype = self.get_cred(ldap_credid)
			cmd.ldap_creds.authtype = 'NTLM'
			cmd.ldap_target = self.get_target(ldap_targetid)

			cmd.smb_creds, stype = self.get_cred(smb_credid)
			cmd.smb_creds.authtype = 'NTLM'
			cmd.smb_target = self.get_target(smb_targetid)
			
			if kerberos_credid == '' or kerberos_credid == None:
				cmd.kerberos_creds = None
			else:
				cmd.kerberos_creds, stype = self.get_cred(kerberos_credid)
				cmd.kerberos_creds.authtype = 'NTLM'
				cmd.kerberos_target = self.get_target(kerberos_targetid)
			
			if dns_target == '' or dns_target is None:
				cmd.dns = self.get_target(ldap_targetid)
			else:
				cmd.dns = self.get_target(dns_target)
			
			cmd.ldap_workers = 4
			cmd.smb_worker_cnt = 100
			cmd.stream_data = True
			
			msg_queue, err = await self.__sr(cmd)
			if err is not None:
				raise err

			while True:
				msg = await msg_queue.get()
				if msg.cmd == NestOpCmd.OK:
					break
				elif msg.cmd == NestOpCmd.ERR:
					raise Exception(msg.reason)
				elif msg.cmd == NestOpCmd.GATHERSTATUS:
					continue
				elif msg.cmd == NestOpCmd.USERRES:
					if msg.kerberoast is True or msg.asreproast is True:
						print(msg)
				else:
					print(msg.cmd)
			return True, None
		except Exception as e:
			traceback.print_exc()
			return False, e

	async def do_loadgraph(self, graphid):
		"""Load graph data from database"""
		try:
			cmd = NestOpLoadGraph()
			cmd.graphid = graphid			
			msg_queue, err = await self.__sr(cmd)
			if err is not None:
				raise err

			while True:
				msg = await msg_queue.get()
				if msg.cmd == NestOpCmd.OK:
					break
				elif msg.cmd == NestOpCmd.ERR:
					raise Exception(msg.reason)
				elif msg.cmd == NestOpCmd.GATHERSTATUS:
					#print(msg)
					continue
				elif msg.cmd == NestOpCmd.USERRES:
					if msg.kerberoast is True or msg.asreproast is True:
						print(msg)
				else:
					print(msg.cmd)

		except Exception as e:
			traceback.print_exc()
			return False, e

	async def do_wsnetrouterconnect(self, url):
		"""Ask the server to create connection to a wsnetrouter"""
		try:
			cmd = NestOpWSNETRouterconnect()
			cmd.url = url
			msg_queue, err = await self.__sr(cmd)
			if err is not None:
				print('Failed to get data. Reason: %s' % err)
				return False, err

			while True:
				msg = await msg_queue.get()
				if msg.cmd == NestOpCmd.OK:
					break
				elif msg.cmd == NestOpCmd.ERR:
					raise Exception(msg.reason)

			return True, None
		except Exception as e:
			traceback.print_exc()
			return False, e
	
	def get_cred(self, credid):
		credid = int(credid)
		creds = NestOpCredsDef()
		creds.adid = self.creds[credid].adid
		creds.sid = self.creds[credid].cid
		return creds, self.creds[credid].stype
	
	def get_target(self, targetid):
		targetid = int(targetid)
		creds = NestOpTargetDef()
		creds.adid = self.targets[targetid].adid
		creds.sid = self.targets[targetid].tid
		return creds

	async def do_smbfiles(self, credid, targetid, agent_id = None, depth = 3, authproto = 'NTLM'):
		"""Starts SMB file enumeration on given host"""
		try:
			if agent_id is None:
				agent_id = self.current_agent
			creds, stype = self.get_cred(credid)
			creds.authtype = authproto
			target = self.get_target(targetid)

			cmd = NestOpSMBFiles()
			cmd.agent_id = agent_id
			cmd.creds = creds
			cmd.target = target
			cmd.depth = depth
			
			msg_queue, err = await self.__sr(cmd)
			if err is not None:
				raise err

			while True:
				msg = await msg_queue.get()
				if msg.cmd == NestOpCmd.OK:
					break
				elif msg.cmd == NestOpCmd.ERR:
					raise Exception(msg.reason)
				elif msg.cmd == NestOpCmd.SMBFILERES:
					print('SMBFile! %s' % msg.unc_path)
			
			return True, None

		except Exception as e:
			traceback.print_exc()
			return False, e

	async def do_smbsessions(self, credid, targetid, authproto = 'NTLM', agent_id = None):
		"""Starts SMB session enumeration on given host"""
		try:
			if agent_id is None:
				agent_id = self.current_agent
			creds, stype = self.get_cred(credid)
			creds.authtype = authproto
			target = self.get_target(targetid)

			cmd = NestOpSMBSessions()
			cmd.agent_id = agent_id
			cmd.creds = creds
			cmd.target = target
			
			msg_queue, err = await self.__sr(cmd)
			if err is not None:
				raise err

			while True:
				msg = await msg_queue.get()
				if msg.cmd == NestOpCmd.OK:
					print('OK!')
					return True, None
				elif msg.cmd == NestOpCmd.ERR:
					raise Exception(msg.reason)
				elif msg.cmd == NestOpCmd.SMBSESSIONRES:
					print('SMBSession! %s' % msg.username)
					

		except Exception as e:
			traceback.print_exc()
			return False, e
	
	async def do_smbdcsync(self, credid, targetid, targetuser_adid, targetuser_sid = None, authproto = 'NTLM', agent_id = None):
		"""Starts SMB dcsync attack. If no targetuser_sid is specified then it means all"""
		try:
			if agent_id is None:
				agent_id = self.current_agent

			creds, stype = self.get_cred(credid)
			creds.authtype = authproto
			target = self.get_target(targetid)

			targetuser = None
			if targetuser_adid is not None and targetuser_adid != '':
				targetuser = NestOpCredsDef()
				targetuser.adid = targetuser_adid
				targetuser.sid = targetuser_sid


			cmd = NestOpSMBDCSync()
			cmd.agent_id = agent_id
			cmd.creds = creds
			cmd.target = target
			cmd.target_user = targetuser
			
			msg_queue, err = await self.__sr(cmd)
			if err is not None:
				raise err

			while True:
				msg = await msg_queue.get()
				if msg.cmd == NestOpCmd.OK:
					print('OK!')
					return True, None
				elif msg.cmd == NestOpCmd.ERR:
					raise Exception(msg.reason)
				elif msg.cmd == NestOpCmd.OBJOWNED:
					print('Owned user! %s' % msg.oid)
					

		except Exception as e:
			traceback.print_exc()
			return False, e
	
	async def do_ldapspns(self, credid, targetid, authproto = 'NTLM', agent_id = None):
		"""Starts SMB dcsync attack. If no targetuser_sid is specified then it means all"""
		try:
			if agent_id is None:
				agent_id = self.current_agent

			creds, stype = self.get_cred(credid)
			creds.authtype = authproto
			target = self.get_target(targetid)

			cmd = NestOpLDAPSPNs()
			cmd.agent_id = agent_id
			cmd.creds = creds
			cmd.target = target
			
			msg_queue, err = await self.__sr(cmd)
			if err is not None:
				raise err

			while True:
				msg = await msg_queue.get()
				if msg.cmd == NestOpCmd.OK:
					print('OK!')
					return True, None
				elif msg.cmd == NestOpCmd.ERR:
					raise Exception(msg.reason)
				elif msg.cmd == NestOpCmd.USERRES:
					print('SPN user! %s' % msg.name)
					

		except Exception as e:
			traceback.print_exc()
			return False, e

	async def do_kerberoast(self, credid, targetid, targetuser_adid, targetuser_sid, agent_id = None):
		"""Starts Kerberoast (spnroast) against a given user"""
		try:
			if agent_id is None:
				agent_id = self.current_agent

			creds, stype = self.get_cred(credid)
			#creds.authtype = authproto
			target = self.get_target(targetid)

			cmd = NestOpKerberoast()
			cmd.agent_id = agent_id
			cmd.creds = creds
			cmd.target = target
			cmd.target_user = NestOpCredsDef()
			cmd.target_user.adid = targetuser_adid
			cmd.target_user.sid = targetuser_sid
			
			msg_queue, err = await self.__sr(cmd)
			if err is not None:
				raise err

			while True:
				msg = await msg_queue.get()
				if msg.cmd == NestOpCmd.OK:
					break
				elif msg.cmd == NestOpCmd.ERR:
					raise Exception(msg.reason)
				elif msg.cmd == NestOpCmd.KERBEROASTRES:
					print('Kerberoast! %s' % msg.ticket)
					
			return True, None
		except Exception as e:
			traceback.print_exc()
			return False, e
	
	async def do_asreproast(self, targetid, targetuser_adid, targetuser_sid, agent_id = None):
		"""Starts ASREProast against a given user"""
		try:
			if agent_id is None:
				agent_id = self.current_agent

			target = self.get_target(targetid)

			target_user = NestOpCredsDef()
			target_user.adid = targetuser_adid
			target_user.sid = targetuser_sid

			cmd = NestOpASREPRoast()
			cmd.agent_id = agent_id
			cmd.target = target
			cmd.target_user = target_user
			
			msg_queue, err = await self.__sr(cmd)
			if err is not None:
				raise err

			while True:
				msg = await msg_queue.get()
				if msg.cmd == NestOpCmd.OK:
					break
				elif msg.cmd == NestOpCmd.ERR:
					raise Exception(msg.reason)
				elif msg.cmd == NestOpCmd.ASREPROASTRES:
					print('Kerberoast! %s' % msg.ticket)
					
			return True, None
		except Exception as e:
			traceback.print_exc()
			return False, e
	
	async def do_gettgt(self, credid, targetid, agent_id = None):
		"""Starts Kerberoast (spnroast) against a given user"""
		try:
			if agent_id is None:
				agent_id = self.current_agent
			creds, stype = self.get_cred(credid)
			#creds.authtype = authproto
			target = self.get_target(targetid)

			cmd = NestOpKerberosTGT()
			cmd.agent_id = agent_id
			cmd.creds = creds
			cmd.target = target
			
			msg_queue, err = await self.__sr(cmd)
			if err is not None:
				raise err

			while True:
				msg = await msg_queue.get()
				if msg.cmd == NestOpCmd.OK:
					break
				elif msg.cmd == NestOpCmd.ERR:
					raise Exception(msg.reason)
				elif msg.cmd == NestOpCmd.KERBEROSTGTRES:
					print('TGT! %s' % msg.ticket)
					
			return True, None
		except Exception as e:
			traceback.print_exc()
			return False, e
	
	async def do_gettgs(self, credid, targetid, spn, agent_id = None):
		"""Starts Kerberoast (spnroast) against a given user"""
		try:
			if agent_id is None:
				agent_id = self.current_agent
			creds, stype = self.get_cred(credid)
			#creds.authtype = authproto
			target = self.get_target(targetid)

			cmd = NestOpKerberosTGS()
			cmd.agent_id = agent_id
			cmd.creds = creds
			cmd.target = target
			cmd.spn = spn
			
			msg_queue, err = await self.__sr(cmd)
			if err is not None:
				raise err

			while True:
				msg = await msg_queue.get()
				if msg.cmd == NestOpCmd.OK:
					break
				elif msg.cmd == NestOpCmd.ERR:
					raise Exception(msg.reason)
				elif msg.cmd == NestOpCmd.KERBEROSTGSRES:
					print('TGT! %s' % msg.ticket)
					
			return True, None
		except Exception as e:
			traceback.print_exc()
			return False, e
	
	async def do_rdpconnect(self, credid, targetid, agent_id = None):
		"""Creates an RDP connection and streams video data"""
		try:
			if agent_id is None:
				agent_id = self.current_agent

			creds, stype = self.get_cred(credid)
			#creds.authtype = authproto
			target = self.get_target(targetid)

			cmd = NestOpRDPConnect()
			cmd.agent_id = agent_id
			cmd.creds = creds
			cmd.target = target
			
			msg_queue, err = await self.__sr(cmd)
			if err is not None:
				raise err

			while True:
				msg = await msg_queue.get()
				if msg.cmd == NestOpCmd.OK:
					break
				elif msg.cmd == NestOpCmd.ERR:
					raise Exception(msg.reason)
				elif msg.cmd == NestOpCmd.RDPRECT:
					print('RDP Rect! %s' % msg.__dict__)
					
			return True, None
		except Exception as e:
			traceback.print_exc()
			return False, e

async def amain(args):
	client = NestWebScoketClientConsole(args.url)

	if len(args.commands) == 0:
		if args.no_interactive is True:
			print('Not starting interactive!')
			return
		await client.run()
	else:
		for command in args.commands:
			cmd = shlex.split(command)
			print(cmd[0])
			if cmd[0] == 'i':
				await client.run()
				return
			res = await client._run_single_command(cmd[0], cmd[1:])
			if res is not None:
				print('Command %s failed, exiting!' % cmd[0])
				return

def main():
	import argparse
	parser = argparse.ArgumentParser(description='Jackdaw WS operator tester')
	parser.add_argument('-v', '--verbose', action='count', default=0, help='Verbosity, can be stacked')
	parser.add_argument('-n', '--no-interactive', action='store_true')
	parser.add_argument('url', help='Connection string in URL format.')
	parser.add_argument('commands', nargs='*')

	args = parser.parse_args()

	asyncio.run(amain(args))


if __name__ == '__main__':
	main()