
import os
import typing
import asyncio
import datetime
import traceback


from jackdaw.nest.ws.utils.hashcatprocess import *
from jackdaw.nest.ws.utils.hashcatprocess.restore import HashcatResoreStruct

from jackdaw.nest.ws.utils.aprocess.aprocess import TextShellProcess
from jackdaw.nest.ws.utils.aprocess import PROCMSGTYPE, PROCMSGSRC, PROCKILL, PROCMSG, PROCMSGLIST, PROCSTOPPED



class HashcatProcess:
	def __init__(self, hashcat_dir:str, wordlists_dir:str, rules_dir:str, hashes_dir:str, executable_name:str):
		self.hashcat_dir:str = hashcat_dir
		self.executable_name:str = executable_name
		self.wordlists_dir:str = wordlists_dir
		self.rules_dir:str = rules_dir
		self.hashes_dir:str = hashes_dir
		
		self.executable_path:str = os.path.join(self.hashcat_dir, self.executable_name)
		self.session_rand:str = '%s%s' % (os.urandom(4).hex(), datetime.datetime.utcnow().strftime("%Y%m%d_%H%M"))
		self.session_name:str = 'session_%s' % self.session_rand
		self.__restore_file:str = os.path.join(self.hashcat_dir, '%s.restore' % self.session_name)

		self.stopped_evt:asyncio.Event = None
		self.out_queue:asyncio.Queue = None
		self.in_queue:asyncio.Queue = None
		self.__in_task:asyncio.Task = None
		self.__poll_task:asyncio.Task = None
		self.__process:TextShellProcess = None
		self.__template_bruteforce = '{executable} -O --quiet --potfile-disable --session %s --force -m {hashtype} -a 3 {hashfile} {mask}' % self.session_name
		self.__template_dictionary = '{executable} -O --quiet --potfile-disable --session %s --force -m {hashtype} -a 0 {hashfile} {wordlist}' % self.session_name
		self.__template_dictionary_rules = '{executable} -O --quiet --potfile-disable --session %s --force -m {hashtype} -a 0 {hashfile} -r {rulefile} {wordlist}' % self.session_name
		self.__template_dictionary_append = '{executable} -O --quiet --potfile-disable --session %s --force -m {hashtype} -a 6 {hashfile} {wordlist} {mask}' % self.session_name
		self.__template_dictionary_prepend = '{executable} -O --quiet --potfile-disable --session %s --force -m {hashtype} -a 7 {hashfile} {mask} {wordlist}' % self.session_name

	
	async def terminate(self):
		try:
			await self.__process.terminate()

		except Exception as e:
			traceback.print_exc()
			return None, e


	async def __process_msgs(self, msgs:typing.List[PROCMSG]):
		try:
			cracked = {}
			error = []
			for msg in msgs:
				await asyncio.sleep(0)
				if msg.src == PROCMSGSRC.STDOUT:
					# here we expect that only cracked hashes with plaintext password will arrive
					line = msg.get_txt().strip()
					if line == '':
						continue
					hashed, plaintext = line.rsplit(':',1)
					cracked[hashed] = plaintext

				else:
					# this came in from stderr, tis is bad
					error.append(msg.get_txt())
					print(msg.get_txt())
			
			if len(cracked) > 0:
				msg = HashcatCracked()
				msg.crackdict = cracked
				await self.out_queue.put(msg)

			# TODO: decide what to do with stderr messages

		except Exception as e:
			traceback.print_exc()
			return None, e

	async def __hashcat_process_in(self):
		try:
			while True:
				result = await self.__process.out_queue.get()
				print(result.type)
				if result.type == PROCMSGTYPE.MSGLIST:
					result = typing.cast(PROCMSGLIST, result)
					await self.__process_msgs(result.msgs)
				elif result.type == PROCMSGTYPE.MSG:
					await self.__process_msgs([result])
				elif result.type == PROCMSGTYPE.STOPPED:
					await self.terminate()
					return
				else:
					print('Unknown message type %s! '% result.type)


		except Exception as e:
			traceback.print_exc()
			return None, e

	def build_command(self, task:HashcatTask):
		try:
			# consolidating wordlists
			wordlists = []
			for wordlist in task.wordlists:
				wordlists.append(os.path.join(self.wordlists_dir, os.path.basename(wordlist)))
			
			
			# writing hashes to file
			if len(task.hashes) == 0:
				raise Exception('No hashes specified!')
			hashfile = 'hashes_%s.txt' % self.session_rand
			hashfile = os.path.join(self.hashes_dir, hashfile)
			with open(hashfile, 'w', newline='') as f:
				for h in task.hashes:
					f.write(h + '\r\n')
			

			# consolidating rulefile
			rulefile = None
			if task.rulefile is not None:
				rulefile = os.path.join(self.rules_dir, os.path.basename(task.rulefile))

			# consolidating hashtype
			hashtype = str(int(str(task.hashtype)))

			# consolidating mask
			mask = task.mask
			
			# constructing command
			crackmode = int(str(task.mode))
			cmd = None
			if crackmode == 0:
				if rulefile is not None:
					cmd = self.__template_dictionary_rules.format(
						executable=self.executable_path, 
						hashtype = hashtype, 
						hashfile = hashfile, 
						rulefile = rulefile,
						wordlist = ' '.join(wordlists)
					)
				else:
					cmd = self.__template_dictionary.format(
						executable=self.executable_path, 
						hashtype = hashtype, 
						hashfile = hashfile, 
						wordlist = ' '.join(wordlists)
					)
			elif crackmode == 3:
				if mask is None:
					raise Exception('Attack mode %s requires mask to be set!' % crackmode)
				cmd = self.__template_bruteforce.format(
						executable=self.executable_path, 
						hashtype = hashtype, 
						hashfile = hashfile, 
						mask = mask
					)
			elif crackmode == 6:
				if mask is None:
					raise Exception('Attack mode %s requires mask to be set!' % crackmode)
				cmd = self.__template_dictionary_append.format(
						executable=self.executable_path, 
						hashtype = hashtype, 
						hashfile = hashfile, 
						mask = mask,
						wordlist = ' '.join(wordlists)
					)
			elif crackmode == 7:
				if mask is None:
					raise Exception('Attack mode %s requires mask to be set!' % crackmode)
				cmd = self.__template_dictionary_prepend.format(
						executable=self.executable_path, 
						hashtype = hashtype, 
						hashfile = hashfile, 
						mask = mask,
						wordlist = ' '.join(wordlists)
					)
			else:
				raise Exception('Unknown crackmode %s' % crackmode)
			
			return cmd, None

		except Exception as e:
			traceback.print_exc()
			return None, e

	async def __status_poll(self, interval = 10):
		await asyncio.sleep(1) # giving time for process to actually start..
		while True:
			try:
				with open(self.__restore_file, 'rb') as f:
					data = f.read()
					restore = HashcatResoreStruct.from_bytes(data)
				
			except Exception as e:
				pass
			
			await asyncio.sleep(interval)


	async def run(self, task:HashcatTask):
		try:
			self.stopped_evt = asyncio.Event()
			self.out_queue = asyncio.Queue()
			command, err = self.build_command(task)
			if err is not None:
				raise err
			print(command)
			self.__process = TextShellProcess(command)
			self.__process_waiter, err = await self.__process.run()
			if err is not None:
				raise err
			
			self.__in_task = asyncio.create_task(self.__hashcat_process_in())
			self.__poll_task = asyncio.create_task(self.__status_poll(int(task.status_interval)))
			return self.stopped_evt.wait(), None
		except Exception as e:
			traceback.print_exc()
			return None, e

async def amain():
	try:
		#task = HashcatTask()
		#task.hashtype = 1000
		#task.hashes = ['0333c27eb4b9401d91fef02a9f74840e']
		#task.mode = 3
		#task.mask = '?a?a?a?a?a?a?a?a'
		#task.wordlists = ['test.txt']
		#task.rulefile = None

		task = HashcatTask()
		task.hashtype = 0
		task.mode = 7
		task.mask = '?a?a?a?a'
		task.wordlists = ['example.dict']
		task.rulefile = None
		task.hashes = []
		with open('/home/devel/Desktop/hashcat-6.2.4/example0.hash') as f:
			for line in f:
				line = line.strip()
				if line == '':
					continue
				task.hashes.append(line)

		hashcat_path = '/home/devel/Desktop/hashcat-6.2.4'
		hashcat_bin = 'hashcat.bin'
		wordlists_dir = '/home/devel/Desktop/hashcat-6.2.4'
		rules_dir = '/home/devel/Desktop/hashcat-6.2.4'
		hashes_dir = '/home/devel/Desktop/hashcat-6.2.4'

		hp = HashcatProcess(hashcat_path, wordlists_dir, rules_dir, hashes_dir, hashcat_bin)
		hpwaiter, err = await hp.run(task)
		if err is not None:
			raise err
		await hpwaiter


	except Exception as e:
		traceback.print_exc()


def main():
	asyncio.run(amain())

if __name__ == '__main__':
	main()