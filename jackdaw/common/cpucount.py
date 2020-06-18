
import os
#import multiprocessing

def get_cpu_count():
	cpu_count = None
	if hasattr(os, 'sched_getaffinity'):
		try:
			cpu_count = len(os.sched_getaffinity(0))
			return cpu_count
		except:
			pass
	
	cpu_count = os.cpu_count()
	if cpu_count is not None:
		return cpu_count
	
	try:
		import multiprocessing
		cpu_count = multiprocessing.cpu_count()
	except:
		pass

	# how hard is to get the cpu count anyways???
	return 4
	