import asyncio
from asyncio import exceptions
import traceback
import shlex
import sys

from jackdaw.nest.ws.utils.aprocess import PROCMSGTYPE, PROCMSGSRC, PROCSTOPPED, PROCMSG, PROCMSGLIST

class TextShellProcess:
	def __init__(self, command:str, kill_timeout:int = 1, encoding:str = sys.stdout.encoding):
		self.commands = shlex.split(command)
		self.kill_timeout = kill_timeout
		self.encoding = encoding
		self.__process = None
		self.in_queue:asyncio.Queue = None
		self.out_queue:asyncio.Queue = None
		self.process_terminated_evt:asyncio.Event = None
		self.returncode:int = None
		self.__handle_in_task = None
		self.__process_stout_task = None
		self.__process_sterr_task = None
		self.__in_buffer = b''
		self.__stdout_buffer = b''
		self.__stderr_buffer = b''

	async def terminate(self):
		try:
			self.__handle_in_task.cancel()
			if self.__process.returncode is None:
				try:
					self.__process.kill()
				except:
					pass
			await asyncio.wait_for(self.__process.wait(), self.kill_timeout)
			self.returncode = self.__process.returncode
			self.__process_comms_task.cancel()
			await self.out_queue.put(PROCSTOPPED(self.returncode))
			self.process_terminated_evt.set()

		except Exception as e:
			traceback.print_exc()
	
	async def __handle_in(self):
		try:
			while True:
				data = await self.in_queue.get()
				if data.type == PROCMSGTYPE.MSG:
					self.__process.stdin.write(data.get_data())
					continue
				elif data.type == PROCMSGTYPE.KILL:
					asyncio.create_task(self.terminate())
					return
				else:
					print('Unknown message type! %s' % data.type)
		except Exception as e:
			traceback.print_exc()

	async def __process_buffers(self, buffer, src = None):
		try:
			if len(buffer) == 0:
				return
			rawlines = buffer.split(b'\n')
			msglist = PROCMSGLIST()
			for lineraw in rawlines[:-1]:
				msglist.msgs.append(PROCMSG(data = lineraw, src = src))
			if len(rawlines[-1]) != -1:
				buffer = rawlines[-1]
			else:
				msglist.msgs.append(PROCMSG(data = rawlines[-1], src = src))
			await self.out_queue.put(msglist)

		except Exception as e:
			traceback.print_exc()

	async def __process_stdout(self):
		try:
			lastrun = False
			pending = None
			while not lastrun:
				if self.__process.returncode is not None:
					lastrun = True

				stdout = await self.__process.stdout.readline()
				self.__stdout_buffer += stdout
					
				await self.__process_buffers(self.__stdout_buffer, src = PROCMSGSRC.STDOUT)
				await asyncio.sleep(0) #in case we get a LOT of data...
				
		except Exception as e:
			traceback.print_exc()
		finally:
			await self.terminate()
	
	async def __process_stderr(self):
		try:
			lastrun = False
			pending = None
			while not lastrun:
				if self.__process.returncode is not None:
					lastrun = True

				stderr = await self.__process.stderr.readline()
				self.__stderr_buffer += stderr
					
				await self.__process_buffers(self.__stderr_buffer, src = PROCMSGSRC.STDERR)
				await asyncio.sleep(0) #in case we get a LOT of data...
				
		except Exception as e:
			traceback.print_exc()
		finally:
			await self.terminate()

	
	async def run(self):
		try:
			self.in_queue = asyncio.Queue()
			self.out_queue = asyncio.Queue()
			self.process_terminated_evt = asyncio.Event()
			self.__process = await asyncio.create_subprocess_exec(
				*self.commands, 
				stdin=asyncio.subprocess.PIPE, 
				stdout=asyncio.subprocess.PIPE, 
				stderr=asyncio.subprocess.PIPE,
				#limit = 10240
				#executable=self.executable
			)

			self.__process_stdout_task = asyncio.create_task(self.__process_stdout())
			self.__process_sterr_task = asyncio.create_task(self.__process_stderr())
			self.__handle_in_task = asyncio.create_task(self.__handle_in())
			return self.process_terminated_evt.wait(), None

		except Exception as e:
			traceback.print_exc()
			return None, e


async def amain():
	try:
		binary = ''
		command = "cat /home/devel/Downloads/words.txt"
		process = TextShellProcess(command)
		pwaiter, err = await process.run()
		if err is not None:
			raise err
		while True:
			data = await process.out_queue.get()
		
		await pwaiter
	
	except Exception as e:
		traceback.print_exc()


def main():
	asyncio.run(amain())

if __name__ == '__main__':
	main()