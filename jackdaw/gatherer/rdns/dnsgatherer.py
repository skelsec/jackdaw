
import copy
import asyncio
from jackdaw import logger
from jackdaw.dbmodel import get_session, windowed_query
from jackdaw.dbmodel.dnslookup import DNSLookup
from jackdaw.dbmodel.adinfo import ADInfo
from jackdaw.dbmodel.adcomp import Machine
from jackdaw.dbmodel.neterror import NetError
from jackdaw.gatherer.progress import GathererProgressType, GathererProgress, MSGTYPE
from sqlalchemy import func


class DNSGatherer:
	def __init__(self, db_conn, ad_id, rdns_resolver, worker_cnt = None, progress_queue = None, stream_data = False):
		self.db_conn = db_conn
		self.ad_id = ad_id
		self.rdns_resolver = rdns_resolver
		self.worker_cnt = worker_cnt
		self.progress_queue = progress_queue
		self.stream_data = stream_data

		self.job_generator_task = None
		self.domain_name = None
		
		
		self.in_q  = asyncio.Queue()
		self.out_q = asyncio.Queue()
		self.rdns_tasks = []
		self.total_targets = None
		self.progress_step_size = 1
		self.prg_hosts_cnt = 0
		self.prg_errors_cnt = 0
		self.session = None


	async def generate_targets(self):
		try:
			q = self.session.query(Machine).filter_by(ad_id = self.ad_id)
			for machine in windowed_query(q, Machine.id, 100):
				try:
					dns_name = machine.dNSHostName
					if dns_name is None or dns_name == '':
						dns_name = '%s.%s' % (str(machine.sAMAccountName[:-1]), str(self.domain_name))
					await self.in_q.put((machine.objectSid, dns_name))
				except:
					continue

			#signaling the ed of target generation
			for _ in range(self.worker_cnt):
				await self.in_q.put(None)
		except Exception as e:
			logger.exception('smb generate_targets')


	async def run(self):
		try:
			self.session = get_session(self.db_conn)
			info = self.session.query(ADInfo).get(self.ad_id)
			self.domain_name = str(info.distinguishedName).replace(',','.').replace('DC=','')
			self.total_targets = self.session.query(func.count(Machine.id)).filter(Machine.ad_id == self.ad_id).scalar()
			self.job_generator_task = asyncio.create_task(self.generate_targets())
			
			for _ in range(self.worker_cnt):
				self.rdns_tasks.append(asyncio.create_task(self.rdns_worker()))

			if self.progress_queue is not None:
				msg = GathererProgress()
				msg.type = GathererProgressType.DNS
				msg.msg_type = MSGTYPE.STARTED
				msg.adid = self.ad_id
				msg.domain_name = self.domain_name
				await self.progress_queue.put(msg)

			while self.total_targets > (self.prg_hosts_cnt + self.prg_errors_cnt):
				await asyncio.sleep(0)
				sid, result, error = await self.out_q.get()
				if error is not None:
					err = NetError()
					err.ad_id = self.ad_id
					err.machine_sid = sid
					err.error = str(error)
					self.session.add(err)
					self.prg_errors_cnt += 1
					continue
				
				self.session.add(result)
				if self.prg_hosts_cnt % self.progress_step_size == 0:
					self.session.commit()

				self.prg_hosts_cnt += 1

				if self.progress_queue is not None:
					if self.prg_hosts_cnt % self.progress_step_size == 0:
						msg = GathererProgress()
						msg.type = GathererProgressType.DNS
						msg.msg_type = MSGTYPE.PROGRESS 
						msg.adid = self.ad_id
						msg.domain_name = self.domain_name
						msg.errors = self.prg_errors_cnt
						msg.total = self.total_targets
						msg.total_finished = self.prg_hosts_cnt
						msg.step_size = self.progress_step_size

						await self.progress_queue.put(msg)

			if self.progress_queue is not None:
				msg = GathererProgress()
				msg.type = GathererProgressType.DNS
				msg.msg_type = MSGTYPE.FINISHED
				msg.adid = self.ad_id
				msg.domain_name = self.domain_name
				await self.progress_queue.put(msg)

			return True, None
		except Exception as e:
			logger.debug('[DNSGatherer] Exception %s' % e)
			return False, e


	async def rdns_worker(self):
		try:
			while True:
				res = await self.in_q.get()
				if res is None:
					return

				sid, dns_name = res
				resolver = copy.deepcopy(self.rdns_resolver)
				ip_addr, err = await resolver.lookup(dns_name)
				if err is not None:
					await self.out_q.put((sid, None, err))
					continue
				result = DNSLookup(self.ad_id, sid, ip_addr, dns_name)
				await self.out_q.put((sid, result, None))

		except asyncio.CancelledError:
			return

		except Exception as e:
			await self.out_q.put((sid, None, e))