
import pathlib

from jackdaw import logger
from jackdaw.gatherer.smb.smb import SMBGatherer
from jackdaw.gatherer.smb.smb_file import SMBShareGathererSettings, ShareGathererManager
from jackdaw.gatherer.ldap.aioldap import LDAPGatherer

from aiosmb.commons.connection.url import SMBConnectionURL
from msldap.commons.url import MSLDAPURLDecoder
from jackdaw.nest.graph.edgecalc import EdgeCalc
from jackdaw.gatherer.rdns.rdns import RDNS


class Gatherer:
	def __init__(self, db_url, work_dir, ldap_url, smb_url, ad_id = None, ldap_worker_cnt = 4, smb_worker_cnt = 100, mp_pool = None, smb_enum_shares = False, smb_gather_types = ['all'], progress_queue = None, show_progress = True):
		self.db_url = db_url
		self.work_dir = work_dir
		self.mp_pool = mp_pool
		self.ldap_worker_cnt = ldap_worker_cnt
		self.smb_worker_cnt = smb_worker_cnt
		self.smb_enum_shares = smb_enum_shares
		self.smb_gather_types = smb_gather_types
		self.ad_id = ad_id
		self.resumption = False
		if ad_id is not None:
			self.resumption = True
		self.smb_url = smb_url
		self.ldap_url = ldap_url
		self.progress_queue = progress_queue
		self.show_progress = show_progress
		self.smb_folder_depth = 1

		self.graph_id = None
		self.ldap_task = None
		self.ldap_mgr = None
		self.ldap_work_dir = None
		self.smb_task = None
		self.smb_mgr = None
		self.smb_work_dir = None
		self.rdns_resolver = None
		

	async def gather_ldap(self):
		try:
			gatherer = LDAPGatherer(
				self.db_url,
				self.ldap_mgr,
				agent_cnt=self.ldap_worker_cnt, 
				work_dir = self.ldap_work_dir,
				progress_queue = self.progress_queue,
				show_progress = self.show_progress
			)
			ad_id, graph_id, err = await gatherer.run()
			if err is not None:
				return None, None, err
			logger.info('ADInfo entry successfully created with ID %s' % ad_id)
			return ad_id, graph_id, None
		except Exception as e:
			return None, None, e

	async def gather_smb(self):
		mgr = SMBGatherer(
			self.smb_mgr, 
			worker_cnt=self.smb_worker_cnt,
			rdns_resolver = self.rdns_resolver
		)
		mgr.gathering_type = self.smb_gather_types
		mgr.db_conn = self.db_url
		mgr.target_ad = self.ad_id
		await mgr.run()

	async def share_enum(self):
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
				show_progress = self.show_progress, 
				progress_queue = self.progress_queue, 
				worker_count = None, 
				mp_pool = self.mp_pool
			)
			res, err = ec.run()
			return res, err
		except Exception as e:
			return False, e

	async def setup(self):
		try:
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
			if self.smb_url is not None:
				self.smb_mgr = SMBConnectionURL(self.smb_url)
			if self.ldap_url is not None:
				self.ldap_mgr = MSLDAPURLDecoder(self.ldap_url)

			logger.debug('Setting up database connection')

			self.rdns_resolver = RDNS(server = self.ldap_mgr.ldap_host, protocol = 'TCP', cache = True)
			
			
			return True, None
		except Exception as e:
			return False, e


	async def run(self):
		try:
			_, err = await self.setup()
			if err is not None:
				return False, err

			if self.ldap_mgr is not None:
				self.ad_id, self.graph_id, err = await self.gather_ldap()
				if err is not None:
					raise err
			if self.smb_url is not None:
				await self.gather_smb()
			
			if self.smb_enum_shares is True and self.smb_url is not None:
				await self.share_enum()
			
			_, err = await self.calc_edges()
			if err is not None:
				raise err
			return True, None
		except Exception as e:
			return False, e



		