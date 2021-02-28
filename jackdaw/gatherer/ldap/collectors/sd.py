
import base64
from hashlib import sha1
from jackdaw.common.cpucount import get_cpu_count
from jackdaw.dbmodel.adsd import JackDawSD
from jackdaw.dbmodel import windowed_query
from jackdaw import logger
from jackdaw.gatherer.progress import *
from jackdaw.gatherer.ldap.agent.common import *
from jackdaw.gatherer.ldap.agent.agent import LDAPGathererAgent
from jackdaw.dbmodel.adgroup import Group
from jackdaw.dbmodel.adinfo import ADInfo
from jackdaw.dbmodel.aduser import ADUser
from jackdaw.dbmodel.adcomp import Machine
from jackdaw.dbmodel.adou import ADOU
from jackdaw.dbmodel.adgpo import GPO
from jackdaw.dbmodel.adtrust import ADTrust
from jackdaw.dbmodel import get_session
from jackdaw.dbmodel.edge import Edge
from jackdaw.dbmodel.edgelookup import EdgeLookup
import gzip
from tqdm import tqdm
import os
import datetime
from sqlalchemy import func
import asyncio
import json


class SDCollector:
	def __init__(self, session, ldap_mgr, ad_id = None, graph_id = None, agent_cnt = None, sd_target_file_handle = None, resumption = False, progress_queue = None, show_progress = True, store_to_db = True):
		self.session = session
		self.ldap_mgr = ldap_mgr
		self.agent_cnt = agent_cnt
		self.ad_id = ad_id
		self.domain_name = None
		self.graph_id = graph_id
		self.sd_target_file_handle = sd_target_file_handle
		self.resumption = resumption
		self.progress_queue = progress_queue
		self.show_progress = show_progress
		self.store_to_db = store_to_db
		self.progress_step_size = 1000
		self.sd_upload_pbar = None

		if self.agent_cnt is None:
			self.agent_cnt = min(get_cpu_count(), 4)

		self.progress_last_updated = datetime.datetime.utcnow()
		self.agent_in_q = None
		self.agent_out_q = None
		self.sd_file = None
		self.sd_file_path = None
		self.total_targets = None
		self.agents = []

	async def store_sd(self, sd):
		if sd['adsec'] is None:
			return
		jdsd = JackDawSD()

		jdsd.ad_id = self.ad_id
		jdsd.guid =  sd['guid']
		jdsd.sid = sd['sid']
		jdsd.object_type = sd['object_type']
		jdsd.sd = base64.b64encode(sd['adsec']).decode()

		jdsd.sd_hash = sha1(sd['adsec']).hexdigest()

		self.sd_file.write(jdsd.to_json().encode() + b'\r\n')
	
	async def resumption_target_gen(self,q, id_filed, obj_type, jobtype):
		for dn, sid, guid in windowed_query(q, id_filed, 10, is_single_entity = False):
			#print(dn)
			data = {
				'dn' : dn,
				'sid' : sid,
				'guid' : guid,
				'object_type' : obj_type
			}
			self.sd_target_file_handle.write(json.dumps(data).encode() + b'\r\n')
			self.total_targets += 1

	async def resumption_target_gen_2(self,q, id_filed, obj_type, jobtype):
		for dn, guid in windowed_query(q, id_filed, 10, is_single_entity = False):
			#print(dn)
			data = {
				'dn' : dn,
				'sid' : None,
				'guid' : guid,
				'object_type' : obj_type
			}
			self.sd_target_file_handle.write(json.dumps(data).encode() + b'\r\n')
			self.total_targets += 1

	async def generate_sd_targets(self):
		try:
			subq = self.session.query(JackDawSD.guid).filter(JackDawSD.ad_id == self.ad_id)
			q = self.session.query(ADInfo.distinguishedName, ADInfo.objectSid, ADInfo.objectGUID).filter_by(id = self.ad_id).filter(~ADInfo.objectGUID.in_(subq))
			await self.resumption_target_gen(q, ADInfo.id, 'domain', LDAPAgentCommand.SDS)
			q = self.session.query(ADUser.dn, ADUser.objectSid, ADUser.objectGUID).filter_by(ad_id = self.ad_id).filter(~ADUser.objectGUID.in_(subq))
			await self.resumption_target_gen(q, ADUser.id, 'user', LDAPAgentCommand.SDS)
			q = self.session.query(Machine.dn, Machine.objectSid, Machine.objectGUID).filter_by(ad_id = self.ad_id).filter(~Machine.objectGUID.in_(subq))
			await self.resumption_target_gen(q, Machine.id, 'machine', LDAPAgentCommand.SDS)
			q = self.session.query(Group.dn, Group.objectSid, Group.objectGUID).filter_by(ad_id = self.ad_id).filter(~Group.objectGUID.in_(subq))
			await self.resumption_target_gen(q, Group.id, 'group', LDAPAgentCommand.SDS)
			q = self.session.query(ADOU.dn, ADOU.objectGUID).filter_by(ad_id = self.ad_id).filter(~ADOU.objectGUID.in_(subq))
			await self.resumption_target_gen_2(q, ADOU.id, 'ou', LDAPAgentCommand.SDS)
			q = self.session.query(GPO.dn, GPO.objectGUID).filter_by(ad_id = self.ad_id).filter(~GPO.objectGUID.in_(subq))
			await self.resumption_target_gen_2(q, GPO.id, 'gpo', LDAPAgentCommand.SDS)

			logger.debug('generate_sd_targets finished!')
		except Exception as e:
			logger.exception('generate_sd_targets')

	async def prepare_targets(self):
		try:
			if self.resumption is True:
				self.total_targets = 1
				if self.sd_target_file_handle is not None:
					raise Exception('Resumption doesnt use the target file handle!') 
				
				self.sd_target_file_handle = gzip.GzipFile('sd_targets','wb')
				await self.generate_sd_targets()

			else:
				self.total_targets = 0
				self.sd_target_file_handle.seek(0,0)
				for line in self.sd_target_file_handle:
					self.total_targets += 1

			return True, None
		
		except Exception as err:
			logger.exception('prep targets')
			return False, err
	
	async def stop_sds_collection(self):
		for _ in range(len(self.agents)):
			await self.agent_in_q.put(None)

		try:
			await asyncio.wait_for(asyncio.gather(*self.agents), 10)
		except asyncio.TimeoutError:
			for agent in self.agents:
				agent.cancel()

		if self.show_progress is True and self.sds_progress is not None:
			self.sds_progress.refresh()
			self.sds_progress.disable = True
		
		if self.progress_queue is not None:
			msg = GathererProgress()
			msg.type = GathererProgressType.SD
			msg.msg_type = MSGTYPE.FINISHED
			msg.adid = self.ad_id
			msg.domain_name = self.domain_name
			await self.progress_queue.put(msg)

		if self.store_to_db is True:
			await self.store_file_data()
	
	async def store_file_data(self):
		try:
			self.progress_last_updated = datetime.datetime.utcnow()
			if self.progress_queue is not None:
				msg = GathererProgress()
				msg.type = GathererProgressType.SDUPLOAD
				msg.msg_type = MSGTYPE.STARTED
				msg.adid = self.ad_id
				msg.domain_name = self.domain_name
				await self.progress_queue.put(msg)

			if self.show_progress is True:
				self.sd_upload_pbar = tqdm(desc='uploading SD to DB', total=self.total_targets)
			if self.sd_file is not None:
				self.sd_file.close()
				cnt = 0
				engine = self.session.get_bind()
				insert_buffer = []
				last_stat_cnt = 0
				with gzip.GzipFile(self.sd_file_path, 'r') as f:
					for line in f:
						line = line.strip()
						if line == '':
							continue
						data = json.loads(line)
						insert_buffer.append(
							{
								'ad_id': int(data['ad_id']),
								'guid' : data['guid'],
								'sid' : data['sid'],
								'object_type' : data['object_type'],
								'sd' : data['sd'],
								'sd_hash' : data['sd_hash']
							}
						)

						#insert_buffer.append(JackDawSD.from_json(line.strip()))
						await asyncio.sleep(0)
						cnt += 1
						if cnt % 100 == 0:
							engine.execute(JackDawSD.__table__.insert(), insert_buffer) #self.session.bulk_save_objects(insert_buffer)
							insert_buffer = []
						if self.show_progress is True:
							self.sd_upload_pbar.update()
						if self.progress_queue is not None and cnt % self.progress_step_size == 0:
							last_stat_cnt += self.progress_step_size
							now = datetime.datetime.utcnow()
							td = (now - self.progress_last_updated).total_seconds()
							self.progress_last_updated = now
							msg = GathererProgress()
							msg.type = GathererProgressType.SDUPLOAD
							msg.msg_type = MSGTYPE.PROGRESS
							msg.adid = self.ad_id
							msg.domain_name = self.domain_name
							msg.total = self.total_targets
							msg.total_finished = cnt
							if td > 0:
								msg.speed = str(self.progress_step_size // td)
							msg.step_size = self.progress_step_size
							await self.progress_queue.put(msg)
							await asyncio.sleep(0)
				
				if len(insert_buffer) > 0:
					engine.execute(JackDawSD.__table__.insert(), insert_buffer) #self.session.bulk_save_objects(insert_buffer)
					insert_buffer = []
				self.session.commit()

				if self.progress_queue is not None:
					now = datetime.datetime.utcnow()
					td = (now - self.progress_last_updated).total_seconds()
					self.progress_last_updated = now
					msg = GathererProgress()
					msg.type = GathererProgressType.SDUPLOAD
					msg.msg_type = MSGTYPE.PROGRESS
					msg.adid = self.ad_id
					msg.domain_name = self.domain_name
					msg.total = self.total_targets
					msg.total_finished = cnt
					if td > 0:
						msg.speed = str((self.total_targets - last_stat_cnt) // td)
					msg.step_size = self.total_targets - last_stat_cnt
					await self.progress_queue.put(msg)
					await asyncio.sleep(0)
			
		except Exception as e:
			logger.exception('Error while uploading sds from file to DB')
			if self.progress_queue is not None:
				msg = GathererProgress()
				msg.type = GathererProgressType.SDUPLOAD
				msg.msg_type = MSGTYPE.ERROR
				msg.adid = self.ad_id
				msg.domain_name = self.domain_name
				msg.error = e
				await self.progress_queue.put(msg)
		finally:
			try:
				os.remove(self.sd_file_path)
			except:
				pass
			
			if self.show_progress is True and self.sd_upload_pbar is not None:
				self.sd_upload_pbar.refresh()
				self.sd_upload_pbar.disable = True

			if self.progress_queue is not None:
				msg = GathererProgress()
				msg.type = GathererProgressType.SDUPLOAD
				msg.msg_type = MSGTYPE.FINISHED
				msg.adid = self.ad_id
				msg.domain_name = self.domain_name
				await self.progress_queue.put(msg)


	async def start_jobs(self):
		self.sd_target_file_handle.seek(0,0)
		for line in self.sd_target_file_handle:
			line = line.strip()
			line = line.decode()
			data = json.loads(line)

			job = LDAPAgentJob(LDAPAgentCommand.SDS, data)
			await self.agent_in_q.put(job)

	async def run(self):
		try:
			
			adinfo = self.session.query(ADInfo).get(self.ad_id)
			self.domain_name = str(adinfo.distinguishedName).replace(',','.').replace('DC=','')
			qs = self.agent_cnt
			self.agent_in_q = asyncio.Queue(qs) #AsyncProcessQueue()
			self.agent_out_q = asyncio.Queue(qs) #AsyncProcessQueue(1000)
			self.sd_file_path = 'sd_' + datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S") + '.gzip'
			self.sd_file = gzip.GzipFile(self.sd_file_path, 'w')

			logger.debug('Polling sds')
			_, res = await self.prepare_targets()
			if res is not None:
				raise res
		
			for _ in range(self.agent_cnt):
				agent = LDAPGathererAgent(self.ldap_mgr, self.agent_in_q, self.agent_out_q)
				self.agents.append(asyncio.create_task(agent.arun()))
			
			asyncio.create_task(self.start_jobs())
			
			if self.show_progress is True:
				self.sds_progress = tqdm(desc='Collecting SDs', total=self.total_targets, position=0, leave=True)
			if self.progress_queue is not None:
				msg = GathererProgress()
				msg.type = GathererProgressType.SD
				msg.msg_type = MSGTYPE.STARTED
				msg.adid = self.ad_id
				msg.domain_name = self.domain_name
				await self.progress_queue.put(msg)			
			
			acnt = self.total_targets
			last_stat_cnt = 0
			while acnt > 0:
				try:
					res = await self.agent_out_q.get()
					res_type, res = res
					
					if res_type == LDAPAgentCommand.SD:
						await self.store_sd(res)
						if self.show_progress is True:
							self.sds_progress.update()
						if self.progress_queue is not None:
							if acnt % self.progress_step_size == 0:
								last_stat_cnt += self.progress_step_size
								now = datetime.datetime.utcnow()
								td = (now - self.progress_last_updated).total_seconds()
								self.progress_last_updated = now
								msg = GathererProgress()
								msg.type = GathererProgressType.SD
								msg.msg_type = MSGTYPE.PROGRESS
								msg.adid = self.ad_id
								msg.domain_name = self.domain_name
								msg.total = self.total_targets
								msg.total_finished = self.total_targets - acnt
								if td > 0:
									msg.speed = str(self.progress_step_size // td)
								msg.step_size = self.progress_step_size
								await self.progress_queue.put(msg)

					elif res_type == LDAPAgentCommand.EXCEPTION:
						logger.warning(str(res))
					
					acnt -= 1
				except Exception as e:
					logger.exception('SDs enumeration error!')
					raise e
			
			if self.progress_queue is not None:
				now = datetime.datetime.utcnow()
				td = (now - self.progress_last_updated).total_seconds()
				self.progress_last_updated = now
				msg = GathererProgress()
				msg.type = GathererProgressType.SD
				msg.msg_type = MSGTYPE.PROGRESS
				msg.adid = self.ad_id
				msg.domain_name = self.domain_name
				msg.total = self.total_targets
				msg.total_finished = self.total_targets
				if td > 0:
					msg.speed = str((self.total_targets - last_stat_cnt) // td)
				msg.step_size = self.total_targets - last_stat_cnt
				await self.progress_queue.put(msg)
			
			
			adinfo = self.session.query(ADInfo).get(self.ad_id)
			adinfo.ldap_sds_finished = True
			self.session.commit()

			return True, None
		except Exception as e:
			logger.exception('SDs enumeration main error')
			if self.progress_queue is not None:
				msg = GathererProgress()
				msg.type = GathererProgressType.SD
				msg.msg_type = MSGTYPE.ERROR
				msg.adid = self.ad_id
				msg.domain_name = self.domain_name
				msg.error = e
				await self.progress_queue.put(msg)
			return False, e
		
		finally:
			await self.stop_sds_collection()
			try:
				self.session.close()
			except:
				pass
