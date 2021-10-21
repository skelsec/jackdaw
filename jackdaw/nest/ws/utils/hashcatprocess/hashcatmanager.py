


import os
import typing
import asyncio
import datetime
import traceback

from jackdaw.nest.ws.protocol import *
from jackdaw.nest.ws.utils.hashcatprocess import *
from jackdaw.nest.ws.utils.hashcatprocess.hashcatprocess import HashcatProcess


class HashcatManager:
	def __init__(self, hashcat_dir:str, wordlists_dir:str, rules_dir:str, hashes_dir:str, executable_name:str):
		self.hashcat_dir:str = hashcat_dir
		self.executable_name:str = executable_name
		self.wordlists_dir:str = wordlists_dir
		self.rules_dir:str = rules_dir
		self.hashes_dir:str = hashes_dir
		self.__process:HashcatProcess = None
		self.__process_stopped_evt:asyncio.Event = None
		self.__process_task = None
		
		self.job_running = False
		self.msg_in_q = None
		self.msg_out_q = None

		self.__msg_in_task = None

	async def __handle_msg_in(self):
		try:
			while True:
				msg = await self.msg_in_q.get()
				print(msg)
				if msg.type == HASHCATCMDTYPE.TASK:
					if self.job_running is True:
						await self.msg_out_q.put(NestOpErr(token = msg.token, reason='Hashcat task already running'))
						continue
					
					self.__process = HashcatProcess(self.hashcat_path, self.wordlists_dir, self.rules_dir, self.hashes_dir, self.hashcat_bin)
					self.__process_stopped_evt, err = await self.__process.run(msg)
					if err is not None:
						raise err
					self.job_running = True
					self.__process_task = asyncio.create_task(self.__handle_process_in(msg.token, self.__process))
				
				if msg.type == HASHCATCMDTYPE.STOP:
					if self.job_running is False:
						await self.msg_out_q.put(NestOpErr(token = msg.token, reason='Hashcat no jobs running'))
						continue
					
					await self.__process.terminate()
					await asyncio.sleep(1)


		except Exception as e:
			return None, e


	async def __handle_process_in(self, token, process):
		try:
			while not self.__process_stopped_evt.is_set():
				msg = await process.out_queue.get()
				print(msg)

		except Exception as e:
			return None, e

	async def run(self):
		try:
			self.msg_in_q = asyncio.Queue()
			self.msg_out_q = asyncio.Queue()
			self.__msg_in_task = asyncio.create_task(self.__handle_msg_in())

		except Exception as e:
			return None, e