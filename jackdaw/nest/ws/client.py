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
			return True, None
		except Exception as e:
			traceback.print_exc()
			return False, e
	
	async def do_getobj(self, oid):
		"""Performs connection"""
		try:			
			cmd = NestOpGetOBJInfo()
			cmd.oid = oid
			print(cmd.to_dict())
			data, err = await self.__sr(cmd)
			if err is not None:
				print('Failed to get object info. Reason: %s' % err)
				return False, err
			print(data)
			return True, None
		except Exception as e:
			traceback.print_exc()
			return False, e

	
	async def do_changead(self, adid):
		"""Changed current AD"""
		try:			
			cmd = NestOpChangeAD()
			cmd.adid = adid
			print(cmd.to_dict())
			_, err = await self.__sr(cmd)
			if err is not None:
				print('Failed to change ADID. Reason: %s' % err)
				return False, err
			
			return True, None
		except Exception as e:
			traceback.print_exc()
			return False, e

	async def do_listad(self):
		"""Lists available ADs"""
		try:			
			cmd = NestOpListAD()
			msg_queue, err = await self.__sr(cmd)
			if err is not None:
				t = traceback.format_tb(err.__traceback__)
				print('Failed to get data. Reason: %s' % t)
				return False, err
			while True:
				msg = await msg_queue.get()
				
				if msg.cmd == NestOpCmd.OK:
					return True, None
				elif msg.cmd == NestOpCmd.ERR:
					print('Error!')
					return False, Exception('Server returned with error')
				elif msg.cmd == NestOpCmd.LISTADSRES:
					print('Available AD_ID: %s' % msg.adids)
			
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
				print('Failed to get data. Reason: %s' % err)
				return False, err

			while True:
				msg = await msg_queue.get()
				if msg.cmd == NestOpCmd.OK:
					return True, None
				elif msg.cmd == NestOpCmd.ERR:
					print('Error!')
					return False, Exception('Server returned with error')
				elif msg.cmd == NestOpCmd.PATHRES:
					print('Available AD_ID: %s' % msg.adids)

			return True, None
		except Exception as e:
			traceback.print_exc()
			return False, e

	async def do_listgraphs(self):
		"""List graphs"""
		try:			
			cmd = NestOpListGraph()
			msg_queue, err = await self.__sr(cmd)
			if err is not None:
				print('Failed to get data. Reason: %s' % err)
				return False, err
			while True:
				msg = await msg_queue.get()
				if msg.cmd == NestOpCmd.OK:
					return True, None
				elif msg.cmd == NestOpCmd.ERR:
					print('Error!')
					return False, Exception('Server returned with error')
				elif msg.cmd == NestOpCmd.LISTGRAPHRES:
					print('AGENT: %s' % msg.gids)
			return True, None
		except Exception as e:
			traceback.print_exc()
			return False, e

	async def do_listagents(self):
		"""List graphs"""
		try:			
			cmd = NestOpListAgents()
			msg_queue, err = await self.__sr(cmd)
			if err is not None:
				print('Failed to get data. Reason: %s' % err)
				return False, err
			while True:
				msg = await msg_queue.get()
				if msg.cmd == NestOpCmd.OK:
					return True, None
				elif msg.cmd == NestOpCmd.ERR:
					print('Error!')
					return False, Exception('Server returned with error')
				elif msg.cmd == NestOpCmd.AGENT:
					print('AGENT: %s' % msg.agentid)

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

	async def do_tcpscan(self, target, ports):
		"""Change current graph"""
		try:
			cmd = NestOpTCPScan()
			cmd.targets = [x for x in target.split(',')]
			cmd.ports = [int(x) for x in ports.split(',')]
			cmd.settings = None
			
			print(cmd.to_dict())
			msg_queue, err = await self.__sr(cmd)
			if err is not None:
				print('Failed to get data. Reason: %s' % err)
				return False, err
			while True:
				msg = await msg_queue.get()
				if msg.cmd == NestOpCmd.OK:
					return True, None
				elif msg.cmd == NestOpCmd.ERR:
					print('Error!')
					return False, Exception('Server returned with error')
				elif msg.cmd == NestOpCmd.TCPSCANRES:
					print(msg)

			return True, None
		except Exception as e:
			traceback.print_exc()
			return False, e
	
	async def do_gather(self, agentid):
		"""Change current graph"""
		try:
			cmd = NestOpGather()
			cmd.agent_id = agentid
			cmd.ldap_url = 'ldap+ntlm-password://TEST\\victim:Passw0rd!1@10.10.10.2'
			cmd.smb_url = 'smb2+ntlm-password://TEST\\victim:Passw0rd!1@10.10.10.2'
			cmd.kerberos_url = 'kerberos+password://TEST\\victim:Passw0rd!1@10.10.10.2'
			cmd.ldap_workers = 4
			cmd.smb_worker_cnt = 500
			cmd.dns = None
			cmd.stream_data = True
			
			msg_queue, err = await self.__sr(cmd)
			if err is not None:
				print('Failed to get data. Reason: %s' % err)
				return False, err

			while True:
				msg = await msg_queue.get()
				if msg.cmd == NestOpCmd.OK:
					print('OK!')
					return True, None
				elif msg.cmd == NestOpCmd.ERR:
					print('Error!')
					return False, Exception('Server returned with error')
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

	async def do_loadgraph(self, graphid):
		"""Load graph data"""
		try:
			cmd = NestOpLoadGraph()
			cmd.graphid = graphid			
			msg_queue, err = await self.__sr(cmd)
			if err is not None:
				print('Failed to get data. Reason: %s' % err)
				return False, err

			while True:
				msg = await msg_queue.get()
				if msg.cmd == NestOpCmd.OK:
					print('OK!')
					return True, None
				elif msg.cmd == NestOpCmd.ERR:
					print('Error!')
					return False, Exception('Server returned with error')
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
		"""Create connection to wsnetrouter"""
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
					print('OK!')
					return True, None
				elif msg.cmd == NestOpCmd.ERR:
					print('Error!')
					return False, Exception('Server returned with error')

		except Exception as e:
			traceback.print_exc()
			return False, e

	async def do_smbfiles(self):
		"""Starts SMB file enumeration on given host"""
		try:
			creds = NestOpCredsDef()
			creds.user_ad_id = None
			creds.user_sid = None
			creds.domain = 'TEST'
			creds.username = 'victim'
			creds.password = 'Passw0rd!1'

			target = NestOpTargetDef()
			target.machine_ad_id = None
			target.machine_sid = None
			target.hostname = None
			target.ip = '10.10.10.2'

			cmd = NestOpSMBFiles()
			cmd.agent_id = '0'
			cmd.creds = creds
			cmd.target = target
			cmd.depth = 3
			
			msg_queue, err = await self.__sr(cmd)
			if err is not None:
				print('Failed to get data. Reason: %s' % err)
				return False, err

			while True:
				msg = await msg_queue.get()
				if msg.cmd == NestOpCmd.OK:
					print('OK!')
					return True, None
				elif msg.cmd == NestOpCmd.ERR:
					print('Error! %s' % msg.reason)
					return False, Exception('Server returned with error')
				elif msg.cmd == NestOpCmd.SMBFILERES:
					print('SMBFile! %s' % msg.unc_path)
					

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