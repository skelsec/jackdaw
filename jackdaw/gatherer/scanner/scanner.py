import asyncio
import ipaddress

from jackdaw.gatherer.scanner.native.agent import TCPPortScan

def parse_target(line):
	if isinstance(line, (ipaddress.IPv4Address, ipaddress.IPv6Address, ipaddress.IPv4Network, ipaddress.IPv6Network)):
		yield line

	try:
		yield ipaddress.ip_address(line)
		return
	except Exception as e:
		print(e)
	
	try:
		for ip in ipaddress.ip_network(line, strict=False):
			yield ip
		return
	except Exception as e:
		print(e)
		pass

	#at this point it's probably a hostname...
	yield line

class ListTarget:
	def __init__(self, targets):
		self.targets = targets

	async def run(self):
		try:
			for line in self.targets:
				line = line.strip()
				if line == '':
					continue
					
				for target in parse_target(line):
					yield target, None

		except Exception as e:
			yield False, e

class FileTarget:
	def __init__(self, filename):
		self.filename = filename

	async def run(self):
		try:
			with open(self.filename, 'r') as f:
				for line in f:
					line = line.strip()
					if line == '':
						continue
					
					for target in parse_target(line):
						yield target, None

		except Exception as e:
			yield False, e

class ScannerWorker:
	def __init__(self, target_q, result_q, backend = 'native'):
		self.target_q = target_q
		self.result_q = result_q
		self.backend = backend
	
	async def run(self):
		try:
			while True:
				data = await self.target_q.get()
				if data is None:
					return
				
				tid, target, port, settings = data
				if self.backend == 'native':
					ps = TCPPortScan(target, port, settings)
					res, err = await ps.run()
					await self.result_q.put((tid, target, port, res, err))
				else:
					raise NotImplementedError()
		except Exception as e:
			print(e)

class JackdawPortScanner:
	def __init__(self, results_queue = None, progress_queue = None, backend = 'native'):
		self.progress_queue = progress_queue
		self.results_queue = results_queue
		self.backend = backend
		self.worker_cnt = 1000
		self.workers = []
		self.target_generators = []
		self.ports = {}
		self.scan_port_timeout = 5
		self.target_q = None
		self.result_q = None
		self.total_target_cnt = 0
		self.finished_target_cnt = 0
		self.tgen_task = None
		self.tgen_finish = None


	def add_target_gen(self, tg):
		self.target_generators.append(tg)

	def add_portrange(self, pr):
		for port in pr:
			self.ports[int(port)] = 1

	async def generate_targets(self):
		try:
			for tg in self.target_generators:
				async for target, err in tg.run():
					if err is not None:
						print('Target generator error: %s' % err)
						continue
					for port in self.ports:
						self.total_target_cnt += 1
						await self.target_q.put((None, target, port, None))
			
		except Exception as e:
			print(e)
		finally:
			self.tgen_finish.set()

	async def run(self):
		try:
			self.target_q = asyncio.Queue(self.worker_cnt)
			self.result_q = asyncio.Queue()
			self.tgen_finish = asyncio.Event()
			
			for _ in range(self.worker_cnt):
				w = ScannerWorker(self.target_q, self.result_q, backend = self.backend)
				self.workers.append(asyncio.create_task(w.run()))
			
			self.tgen_task = asyncio.create_task(self.generate_targets())
			await asyncio.sleep(0)
			while True:
				if self.tgen_finish.is_set() and (self.total_target_cnt == self.finished_target_cnt):
					break

				res = await self.result_q.get()
				self.finished_target_cnt += 1
				
				if self.progress_queue is not None:
					await self.progress_queue.put(None)
				
				if self.results_queue is not None:
					await self.results_queue.put(res)

			self.tgen_task.cancel()
			for _ in range(len(self.workers)):
				await self.target_q.put(None)
			
			for worker in self.workers:
				worker.cancel()
			
			return True, None

		except Exception as e:
			return False, e

async def amain():
	ports = [22,445,80,8080]
	tg = ListTarget(['192.168.30.1/24'])
	ps = JackdawPortScanner()
	ps.add_portrange(ports)
	ps.add_target_gen(tg)
	_, err = await ps.run()
	if err is not None:
		print(err)
	print(2)


def main():
	asyncio.run(amain())

if __name__ == '__main__':
	main()

	


	