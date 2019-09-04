from multiprocessing import Manager, cpu_count
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import asyncio

def AsyncProcessQueue(maxsize=0):
	m = Manager()
	q = m.Queue(maxsize=maxsize)
	return _ProcQueue(q)   

class _ProcQueue(object):
	def __init__(self, q):
		self._queue = q
		self._real_executor = None
		self._cancelled_join = False

	@property
	def _executor(self):
		if not self._real_executor:
			self._real_executor = ThreadPoolExecutor(max_workers=cpu_count())
		return self._real_executor

	def __getstate__(self):
		self_dict = self.__dict__
		self_dict['_real_executor'] = None
		return self_dict

	def __getattr__(self, name):
		if name in ['qsize', 'empty', 'full', 'put', 'put_nowait',
					'get', 'get_nowait', 'close']:
			return getattr(self._queue, name)
		else:
			raise AttributeError("'%s' object has no attribute '%s'" % 
									(self.__class__.__name__, name))

	@asyncio.coroutine
	def coro_put(self, item):
		loop = asyncio.get_event_loop()
		return (yield from loop.run_in_executor(self._executor, self.put, item))

	@asyncio.coroutine    
	def coro_get(self):
		loop = asyncio.get_event_loop()
		return (yield from loop.run_in_executor(self._executor, self.get))

	def cancel_join_thread(self):
		self._cancelled_join = True
		self._queue.cancel_join_thread()

	def join_thread(self):
		self._queue.join_thread()
		if self._real_executor and not self._cancelled_join:
			self._real_executor.shutdown()
