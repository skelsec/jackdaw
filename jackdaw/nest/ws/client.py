import asyncio
import traceback
import shlex

import websockets

from jackdaw.external.aiocmd.aiocmd import aiocmd
from jackdaw import logger

from jackdaw.nest.ws.operator.protocol import *


class CMDEvent:
	def __init__(self, reply = None, arrived_evt = None):
		self.reply = reply
		self.arrived_evt = arrived_evt

class NestWebScoketClientConsole(aiocmd.PromptToolkitCmd):
	def __init__(self, url):
		aiocmd.PromptToolkitCmd.__init__(self, ignore_sigint=False) #Setting this to false, since True doesnt work on windows...
		self.url = url
		self.reply_dispatch_table = {}
		self.token_ctr = 0
		self.ad_id = None
		self.handle_in_task = None
		self.websocket = None


	async def __handle_in(self):
		while True:
			try:
				print(1)
				data = await self.websocket.recv()
				print('DATA IN -> %s' % data)
				cmd = NestOpCmdDeserializer.from_json(data)
				if cmd.cmd == NestOpCmd.LOG:
					print('LOG!')
					continue
				if cmd.token not in self.reply_dispatch_table:
					print('Unknown reply arrived! %s' % cmd)

				self.reply_dispatch_table[cmd.token].data = cmd
				self.reply_dispatch_table[cmd.token].arrived_evt.set()

			except Exception as e:
				print('Reciever error %s' % e)
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
			cmd.token = self.__get_token()
			ce = CMDEvent(None, asyncio.Event())
			self.reply_dispatch_table[cmd.token] = ce
			await self.websocket.send(cmd.to_json())
			await ce.arrived_evt.wait()

			reply = ce.data
			del self.reply_dispatch_table[cmd.token]
			if reply.cmd == NestOpCmd.ERR:
				if reply.reason is None:
					reply.reason = 'Unknown'
				return None, reply.reason
			elif reply.cmd == NestOpCmd.OK:
				return True, None
			
			return reply.data, None
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
			data, err = await self.__sr(cmd)
			if err is not None:
				print('Failed to get data. Reason: %s' % err)
				return False, err
			for i in data:
				print('Available AD_ID: %s' % i)
			return True, None
		except Exception as e:
			traceback.print_exc()
			return False, e

	async def do_pathda(self):
		"""Calculates all paths to DA"""
		try:			
			cmd = NestOpPathDA()
			data, err = await self.__sr(cmd)
			if err is not None:
				print('Failed to get data. Reason: %s' % err)
				return False, err
			print(data)
			return True, None
		except Exception as e:
			traceback.print_exc()
			return False, e

	async def do_listgraphs(self):
		"""List graphs"""
		try:			
			cmd = NestOpListGraphs()
			data, err = await self.__sr(cmd)
			if err is not None:
				print('Failed to get data. Reason: %s' % err)
				return False, err
			print(data)
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
			data, err = await self.__sr(cmd)
			if err is not None:
				print('Failed to get data. Reason: %s' % err)
				return False, err
			print(data)
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
			res = await client._run_single_command(cmd[0], cmd[1:])
			if res is not None:
				print('Command %s failed, exiting!' % cmd[0])
				return

def main():
	import argparse
	parser = argparse.ArgumentParser(description='MS LDAP library')
	parser.add_argument('-v', '--verbose', action='count', default=0, help='Verbosity, can be stacked')
	parser.add_argument('-n', '--no-interactive', action='store_true')
	parser.add_argument('url', help='Connection string in URL format.')
	parser.add_argument('commands', nargs='*')

	args = parser.parse_args()

	asyncio.run(amain(args))


if __name__ == '__main__':
	main()