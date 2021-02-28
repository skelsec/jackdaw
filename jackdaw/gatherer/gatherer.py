
import pathlib
import asyncio
import platform

from jackdaw import logger
from jackdaw.gatherer.smb.smb import SMBGatherer
from jackdaw.gatherer.ldap.aioldap import LDAPGatherer
from jackdaw.gatherer.kerberos.kerberos import KerberoastGatherer

from aiosmb.commons.connection.url import SMBConnectionURL
from msldap.commons.url import MSLDAPURLDecoder
from jackdaw.gatherer.edgecalc import EdgeCalc
from jackdaw.gatherer.rdns.rdns import RDNS
from jackdaw.gatherer.rdns.dnsgatherer import DNSGatherer
from tqdm import tqdm
from jackdaw.gatherer.progress import *

class Gatherer:
	def __init__(self, db_url, work_dir, ldap_url, smb_url, kerb_url = None, ad_id = None, calc_edges = True, ldap_worker_cnt = 4, smb_worker_cnt = 100, mp_pool = None, smb_enum_shares = False, smb_gather_types = ['all'], progress_queue = None, show_progress = True, dns = None, store_to_db = True, graph_id = None, stream_data = False, no_work_dir = False):
		self.db_url = db_url
		self.work_dir = work_dir
		self.no_work_dir = no_work_dir
		self.mp_pool = mp_pool
		self.ldap_worker_cnt = ldap_worker_cnt
		self.smb_worker_cnt = smb_worker_cnt
		self.smb_enum_shares = smb_enum_shares
		self.smb_gather_types = smb_gather_types
		self.ad_id = ad_id
		self.calculate_edges = calc_edges
		self.dns_server = dns
		self.store_to_db = store_to_db
		self.resumption = False
		if ad_id is not None:
			self.resumption = True

		self.smb_url = smb_url
		self.ldap_url = ldap_url
		self.kerb_url = kerb_url
		self.progress_queue = progress_queue
		self.show_progress = show_progress
		self.smb_folder_depth = 1

		self.graph_id = graph_id
		self.ldap_task = None
		self.ldap_mgr = None
		self.ldap_work_dir = None
		self.smb_task = None
		self.smb_mgr = None
		self.smb_work_dir = None
		self.rdns_resolver = None
		self.progress_task = None
		self.base_collection_finish_evt = None

		self.smb_early_task = None
		self.ldap_gatherer = None
		self.progress_refresh_task = None
		self.progress_bars = []
		self.stream_data = stream_data

	
	async def progress_refresh(self):
		while True:
			msg = GathererProgress()
			msg.type = GathererProgressType.REFRESH
			msg.msg_type = MSGTYPE.PROGRESS
			await self.progress_queue.put(msg)
			await asyncio.sleep(10)

	async def print_progress(self):
		if self.show_progress is False:
			try:
				while True:
					msg = await self.progress_queue.get()
					if msg is None:
						return
					continue
			except Exception as e:
				logger.exception('Progress bar crashed')

		logger.debug('Setting up progress bars')
		pos = 0
		ldap_info_pbar        = tqdm(desc = 'MSG:  ', ascii=True, position=pos)
		self.progress_bars.append(ldap_info_pbar)
		pos += 1
		if self.ldap_url is not None:
			ldap_basic_pbar        = tqdm(desc = 'LDAP basic enum       ', ascii=True, position=pos)
			self.progress_bars.append(ldap_basic_pbar)
			pos += 1
			ldap_sd_pbar           = tqdm(desc = 'LDAP SD enum          ', ascii=True, position=pos)
			self.progress_bars.append(ldap_sd_pbar)
			pos += 1
			if self.store_to_db is True:
				ldap_sdupload_pbar     = tqdm(desc = 'LDAP SD upload        ', ascii=True, position=pos)
				self.progress_bars.append(ldap_sdupload_pbar)
				pos += 1
			ldap_member_pbar       = tqdm(desc = 'LDAP membership enum  ', ascii=True, position=pos)
			self.progress_bars.append(ldap_member_pbar)
			pos += 1
			if self.store_to_db is True:
				ldap_memberupload_pbar = tqdm(desc = 'LDAP membership upload', ascii=True, position=pos)
				self.progress_bars.append(ldap_memberupload_pbar)
				pos += 1
		if self.kerb_url is not None:
			kerb_pbar               = tqdm(desc = 'KERBEROAST            ', ascii=True, position=pos)
			self.progress_bars.append(kerb_pbar)
			pos += 1
		if self.rdns_resolver is not None:
			dns_pbar               = tqdm(desc = 'DNS enum              ', ascii=True, position=pos)
			self.progress_bars.append(dns_pbar)
			pos += 1
		if self.smb_url is not None:
			smb_pbar               = tqdm(desc = 'SMB enum              ', ascii=True, position=pos)
			self.progress_bars.append(smb_pbar)
			pos += 1
		if self.calculate_edges is True:
			sdcalc_pbar            = tqdm(desc = 'SD edges calc         ', ascii=True, position=pos)
			self.progress_bars.append(sdcalc_pbar)
			pos += 1
			sdcalcupload_pbar      = tqdm(desc = 'SD edges upload       ', ascii=True, position=pos)
			self.progress_bars.append(sdcalcupload_pbar)
			pos += 1

		self.progress_refresh_task = asyncio.create_task(self.progress_refresh())
		
		logger.debug('waiting for progress messages')
		while True:
			try:
				msg = await self.progress_queue.get()
				
				if msg is None:
					for pbar in self.progress_bars:
						pbar.refresh()
					return
			
				if msg.type == GathererProgressType.BASIC:
					if msg.msg_type == MSGTYPE.PROGRESS:
						if ldap_basic_pbar.total is None:
							ldap_basic_pbar.total = msg.total
						
						ldap_basic_pbar.update(msg.step_size)

					if msg.msg_type == MSGTYPE.FINISHED:
						ldap_basic_pbar.refresh()

				elif msg.type == GathererProgressType.SD:
					if msg.msg_type == MSGTYPE.PROGRESS:
						if ldap_sd_pbar.total is None:
							ldap_sd_pbar.total = msg.total
						
						ldap_sd_pbar.update(msg.step_size)

					if msg.msg_type == MSGTYPE.FINISHED:
						ldap_sd_pbar.refresh()

				elif msg.type == GathererProgressType.SDUPLOAD:
					if msg.msg_type == MSGTYPE.PROGRESS:
						if ldap_sdupload_pbar.total is None:
							ldap_sdupload_pbar.total = msg.total
						
						ldap_sdupload_pbar.update(msg.step_size)

					if msg.msg_type == MSGTYPE.FINISHED:
						ldap_sdupload_pbar.refresh()

				elif msg.type == GathererProgressType.MEMBERS:
					if msg.msg_type == MSGTYPE.PROGRESS:
						if ldap_member_pbar.total is None:
							ldap_member_pbar.total = msg.total
						
						ldap_member_pbar.update(msg.step_size)

					if msg.msg_type == MSGTYPE.FINISHED:
						ldap_member_pbar.refresh()
				
				elif msg.type == GathererProgressType.MEMBERSUPLOAD:
					if msg.msg_type == MSGTYPE.PROGRESS:
						if ldap_memberupload_pbar.total is None:
							ldap_memberupload_pbar.total = msg.total
						
						ldap_memberupload_pbar.update(msg.step_size)

					if msg.msg_type == MSGTYPE.FINISHED:
						ldap_memberupload_pbar.refresh()

				elif msg.type == GathererProgressType.KERBEROAST:
					if msg.msg_type == MSGTYPE.PROGRESS:
						if kerb_pbar.total is None:
							kerb_pbar.total = msg.total
						
						kerb_pbar.update(msg.step_size)

					if msg.msg_type == MSGTYPE.FINISHED:
						kerb_pbar.refresh()

				elif msg.type == GathererProgressType.DNS:
					if msg.msg_type == MSGTYPE.PROGRESS:
						if dns_pbar.total is None:
							dns_pbar.total = msg.total
						
						dns_pbar.update(msg.step_size)

					if msg.msg_type == MSGTYPE.FINISHED:
						dns_pbar.refresh()
				
				elif msg.type == GathererProgressType.SMB:
					if msg.msg_type == MSGTYPE.PROGRESS:
						if smb_pbar.total is None:
							smb_pbar.total = msg.total
						
						smb_pbar.update(msg.step_size)

					if msg.msg_type == MSGTYPE.FINISHED:
						smb_pbar.refresh()

				elif msg.type == GathererProgressType.SDCALC:
					if msg.msg_type == MSGTYPE.PROGRESS:
						if sdcalc_pbar.total is None:
							sdcalc_pbar.total = msg.total
						
						sdcalc_pbar.update(msg.step_size)

					if msg.msg_type == MSGTYPE.FINISHED:
						sdcalc_pbar.refresh()

				elif msg.type == GathererProgressType.SDCALCUPLOAD:
					if msg.msg_type == MSGTYPE.PROGRESS:
						if sdcalcupload_pbar.total is None:
							sdcalcupload_pbar.total = msg.total
						
						sdcalcupload_pbar.update(msg.step_size)

					if msg.msg_type == MSGTYPE.FINISHED:
						sdcalcupload_pbar.refresh()

				elif msg.type == GathererProgressType.INFO:
					ldap_info_pbar.display('MSG: %s' % str(msg.text))

				elif msg.type == GathererProgressType.REFRESH:
					for pbar in self.progress_bars:
						pbar.refresh()

			except asyncio.CancelledError:
				return
			except Exception as e:
				logger.exception('Progress bar crashed')
				return

	async def gather_ldap(self):
		try:
			self.ldap_gatherer = LDAPGatherer(
				self.db_url,
				self.ldap_mgr,
				agent_cnt=self.ldap_worker_cnt, 
				work_dir = self.ldap_work_dir,
				progress_queue = self.progress_queue,
				show_progress = False,
				ad_id = self.ad_id, #this should be none, or resumption is indicated!
				store_to_db = self.store_to_db,
				base_collection_finish_evt = self.base_collection_finish_evt,
				stream_data = self.stream_data,
				no_work_dir=self.no_work_dir
			)
			ad_id, graph_id, err = await self.ldap_gatherer.run()
			if err is not None:
				return None, None, err
			logger.debug('ADInfo entry successfully created with ID %s' % ad_id)
			return ad_id, graph_id, None
		except Exception as e:
			return None, None, e

	async def kerberoast(self):
		try:
			gatherer = KerberoastGatherer(
				self.db_url, 
				self.ad_id, 
				progress_queue = self.progress_queue,
				show_progress = False,
				kerb_url = self.kerb_url,
				domain_name = None
			)
			_, err = await gatherer.run()
			if err is not None:
				raise err

			return True, None
		except Exception as e:
			return None, e

	async def gather_smb(self):
		try:
			mgr = SMBGatherer(
				self.db_url,
				self.ad_id,
				self.smb_mgr, 
				worker_cnt=self.smb_worker_cnt,
				progress_queue = self.progress_queue,
				show_progress = False,
				stream_data = self.stream_data
			)
			mgr.gathering_type = self.smb_gather_types
			mgr.target_ad = self.ad_id
			res, err = await mgr.run()
			return res, err
		except Exception as e:
			return None, e

	async def gather_dns(self):
		try:
			mgr = DNSGatherer(
				self.db_url,
				self.ad_id,
				self.rdns_resolver,
				worker_cnt = 100,
				progress_queue = self.progress_queue,
				stream_data = self.stream_data,
			)			
			res, err = await mgr.run()
			return res, err

		except Exception as e:
			return None, e

	async def share_enum(self):
		from jackdaw.gatherer.smb.smb_file import SMBShareGathererSettings, ShareGathererManager
		settings_base = SMBShareGathererSettings(self.ad_id, self.smb_mgr, None, None, None)
		settings_base.dir_depth = self.smb_folder_depth
		mgr = ShareGathererManager(settings_base, db_conn = self.db_conn, worker_cnt = args.smb_workers)
		mgr.run()

	async def calc_edges(self):
		try:
			ec = EdgeCalc(
				self.db_url, 
				self.ad_id, 
				self.graph_id, 
				buffer_size = 100, 
				show_progress = False, 
				progress_queue = self.progress_queue, 
				worker_count = None, 
				mp_pool = self.mp_pool,
				work_dir=self.work_dir if self.no_work_dir is False else None
			)
			res, err = await ec.run()
			return res, err
		except Exception as e:
			return False, e

	async def setup(self):
		try:
			if self.no_work_dir is False:
				logger.debug('Setting up working directory')
				if self.work_dir is not None:
					if isinstance(self.work_dir, str):
						self.work_dir = pathlib.Path(self.work_dir)
				else:
					self.work_dir = pathlib.Path()

				self.work_dir.mkdir(parents=True, exist_ok=True)
				self.ldap_work_dir = self.work_dir.joinpath('ldap')
				self.ldap_work_dir.mkdir(parents=True, exist_ok=True)
				self.smb_work_dir = self.work_dir.joinpath('smb')
				self.smb_work_dir.mkdir(parents=True, exist_ok=True)


			logger.debug('Setting up connection objects')
			
			if self.dns_server is not None:
				self.rdns_resolver = RDNS(server = self.dns_server, protocol = 'TCP', cache = True)
			
			if self.ldap_url is not None:
				self.ldap_mgr = MSLDAPURLDecoder(self.ldap_url)
				if self.rdns_resolver is None:
					self.rdns_resolver = RDNS(server = self.ldap_mgr.ldap_host, protocol = 'TCP', cache = True)

			if self.smb_url is not None:
				self.smb_mgr = SMBConnectionURL(self.smb_url)
				if self.rdns_resolver is None:
					self.rdns_resolver = RDNS(server = self.smb_mgr.ip, protocol = 'TCP', cache = True)
			

			logger.debug('Setting up database connection')

			if self.progress_queue is None and self.show_progress is True:
				self.progress_queue = asyncio.Queue()
				self.progress_task = asyncio.create_task(self.print_progress())
			
			return True, None
		except Exception as e:
			return False, e

	async def run(self):
		try:
			_, err = await self.setup()
			if err is not None:
				raise err

			if self.ldap_mgr is not None:
				self.ad_id, self.graph_id, err = await self.gather_ldap()
				if err is not None:
					raise err
			
			if self.kerb_url is not None:
				_, err = await self.kerberoast()
				if err is not None:
					logger.error('Kerberos did not work... %s' % err)

			if self.rdns_resolver is not None:
				_, err = await self.gather_dns()
				if err is not None:
					logger.error('DNS lookup did not work... %s' % err)

			if self.smb_url is not None:
				_, err = await self.gather_smb()
				if err is not None:
					raise err
				
			if self.smb_enum_shares is True and self.smb_url is not None:
				_, err = await self.share_enum()
				if err is not None:
					raise err
				
			if self.calculate_edges is True and self.store_to_db is True:
				_, err = await self.calc_edges()
				if err is not None:
					raise err

			if self.progress_queue is not None:
				msg = GathererProgress()
				msg.type = GathererProgressType.INFO
				msg.msg_type = MSGTYPE.FINISHED
				msg.adid = self.ad_id
				msg.text = 'Gatherer finished!'
				await self.progress_queue.put(msg)


			return True, None
		except Exception as e:
			return False, e

		finally:
			if self.progress_queue is not None:
				await self.progress_queue.put(None)
			if self.show_progress is True and self.progress_queue is None and self.progress_task is not None:
				try:
					await asyncio.wait_for(asyncio.gather(*[self.progress_task]), 1)
				except asyncio.TimeoutError:
					self.progress_task.cancel()
				
				if self.progress_refresh_task is not None:
					self.progress_refresh_task.cancel()



		