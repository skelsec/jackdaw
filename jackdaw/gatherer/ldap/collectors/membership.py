
import os
import gzip
import json
import datetime
import asyncio

from jackdaw.common.cpucount import get_cpu_count
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
from jackdaw.dbmodel.utils.tokengroup import JackDawTokenGroup
from jackdaw.dbmodel import get_session
from jackdaw.dbmodel.edge import Edge
from jackdaw.dbmodel.edgelookup import EdgeLookup
from jackdaw.dbmodel import windowed_query
from jackdaw import logger

from tqdm import tqdm
from sqlalchemy import func


class MembershipCollector:
	def __init__(self, session, ldap_mgr, ad_id = None, agent_cnt = None, progress_queue = None, show_progress = True, graph_id = None, resumption = False, members_target_file_handle = None, store_to_db = True):
		self.session = session
		self.ldap_mgr = ldap_mgr
		self.agent_cnt = agent_cnt
		self.ad_id = ad_id
		self.graph_id = graph_id
		self.domain_name = None
		self.resumption = resumption
		self.members_target_file_handle = members_target_file_handle
		
		self.progress_queue = progress_queue
		self.show_progress = show_progress

		if self.agent_cnt is None:
			self.agent_cnt = min(get_cpu_count(), 8)

		self.member_finish_ctr = 0
		self.agent_in_q = None
		self.agent_out_q = None
		self.total_targets = 0
		self.total_members_to_poll = 0
		self.progress_last_updated = datetime.datetime.utcnow()
		self.agents = []
		self.progress_step_size = 1000
		self.lookup = {}
		self.store_to_db = store_to_db

	def sid_to_id_lookup(self, sid, ad_id, object_type):
		if sid in self.lookup:
			return self.lookup[sid]

		src_id = self.session.query(EdgeLookup.id).filter_by(oid = sid).filter(EdgeLookup.ad_id == ad_id).first()
		if src_id is None:
			t = EdgeLookup(ad_id, sid, object_type)
			self.session.add(t)
			self.session.commit()
			self.session.refresh(t)
			src_id = t.id
			self.lookup[sid] = src_id
		else:
			src_id = src_id[0]
			self.lookup[sid] = src_id
		return src_id

	async def resumption_target_gen_member(self,q, id_filed, obj_type, jobtype):
		for dn, sid, guid in windowed_query(q, id_filed, 10, is_single_entity = False):
			#print(dn)
			data = {
				'dn' : dn,
				'sid' : sid,
				'guid' : guid,
				'object_type' : obj_type
			}
			self.members_target_file_handle.write(json.dumps(data).encode() + b'\r\n')
			self.total_members_to_poll += 1

	async def generate_member_targets(self):
		try:
			subq = self.session.query(EdgeLookup.oid).filter_by(ad_id = self.ad_id).filter(EdgeLookup.id == Edge.src).filter(Edge.label == 'member').filter(Edge.ad_id == self.ad_id)
			q = self.session.query(ADUser.dn, ADUser.objectSid, ADUser.objectGUID)\
				.filter_by(ad_id = self.ad_id)\
				.filter(~ADUser.objectSid.in_(subq))
			await self.resumption_target_gen_member(q, ADUser.id, 'user', LDAPAgentCommand.MEMBERSHIPS)
			q = self.session.query(Machine.dn, Machine.objectSid, Machine.objectGUID)\
				.filter_by(ad_id = self.ad_id)\
				.filter(~Machine.objectSid.in_(subq))
			await self.resumption_target_gen_member(q, Machine.id, 'machine', LDAPAgentCommand.MEMBERSHIPS)
			q = self.session.query(Group.dn, Group.objectSid, Group.objectGUID)\
				.filter_by(ad_id = self.ad_id)\
				.filter(~Group.objectSid.in_(subq))
			await self.resumption_target_gen_member(q, Group.id, 'group', LDAPAgentCommand.MEMBERSHIPS)
			
		except Exception as e:
			logger.exception('generate_member_targets')
			

	async def stop_memberships_collection(self):
		for _ in range(len(self.agents)):
			await self.agent_in_q.put(None)


		try:
			await asyncio.wait_for(asyncio.gather(*self.agents), 10)
		except asyncio.TimeoutError:
			for agent in self.agents:
				agent.cancel()
		
		
		if self.show_progress is True:
			self.member_progress.refresh()
			self.member_progress.disable = True

		if self.progress_queue is not None:
			msg = GathererProgress()
			msg.type = GathererProgressType.MEMBERS
			msg.msg_type = MSGTYPE.FINISHED
			msg.adid = self.ad_id
			msg.domain_name = self.domain_name
			await self.progress_queue.put(msg)
		
		if self.store_to_db is True:
			await self.store_file_data()

	async def store_file_data(self):
		try:
			if self.progress_queue is not None:
				msg = GathererProgress()
				msg.type = GathererProgressType.MEMBERSUPLOAD
				msg.msg_type = MSGTYPE.STARTED
				msg.adid = self.ad_id
				msg.domain_name = self.domain_name
				await self.progress_queue.put(msg)

			if self.show_progress is True:
				self.upload_pbar = tqdm(desc='Uploading memberships to DB', total=self.member_finish_ctr)

			self.token_file.close()
			cnt = 0
			last_stat_cnt = 0
			engine = self.session.get_bind()
			insert_buffer = []

			with gzip.GzipFile(self.token_file_path, 'r') as f:
				for line in f:
					line = line.strip()
					if line  == '':
						continue
					data = json.loads(line)
					src_id = self.sid_to_id_lookup(data['sid'], int(data['ad_id']), data['object_type'])
					dst_id = self.sid_to_id_lookup(data['member_sid'], int(data['ad_id']), data['object_type'])

					#edge = Edge(sd.ad_id, self.graph_id, src_id, dst_id, 'member')

					insert_buffer.append(
						{
							"ad_id": int(data['ad_id']),
							'graph_id' : self.graph_id,
							'src' : src_id,
							'dst' : dst_id,
							'label' : 'member'
						}
					)

					#self.session.add(edge)
					await asyncio.sleep(0)
					cnt += 1
					if cnt % 10000 == 0:
						engine.execute(Edge.__table__.insert(), insert_buffer)
						insert_buffer = []

					if self.show_progress is True:
						self.upload_pbar.update()
					
					if self.progress_queue is not None and cnt % self.progress_step_size == 0:
						last_stat_cnt += self.progress_step_size
						now = datetime.datetime.utcnow()
						td = (now - self.progress_last_updated).total_seconds()
						self.progress_last_updated = now
						msg = GathererProgress()
						msg.type = GathererProgressType.MEMBERSUPLOAD
						msg.msg_type = MSGTYPE.PROGRESS
						msg.adid = self.ad_id
						msg.domain_name = self.domain_name
						msg.total = self.member_finish_ctr
						msg.total_finished = cnt
						if td > 0:
							msg.speed = str(self.progress_step_size // td)
						msg.step_size = self.progress_step_size
						await self.progress_queue.put(msg)

			if len(insert_buffer) > 0:
				engine.execute(Edge.__table__.insert(), insert_buffer)
				insert_buffer = []

			if self.progress_queue is not None:
				now = datetime.datetime.utcnow()
				td = (now - self.progress_last_updated).total_seconds()
				self.progress_last_updated = now
				msg = GathererProgress()
				msg.type = GathererProgressType.MEMBERSUPLOAD
				msg.msg_type = MSGTYPE.PROGRESS
				msg.adid = self.ad_id
				msg.domain_name = self.domain_name
				msg.total = self.member_finish_ctr
				msg.total_finished = cnt
				if td > 0:
					msg.speed = str((self.member_finish_ctr - last_stat_cnt) // td)
				msg.step_size = self.member_finish_ctr - last_stat_cnt
				await self.progress_queue.put(msg)

			self.session.commit()
			if self.progress_queue is not None:
				msg = GathererProgress()
				msg.type = GathererProgressType.MEMBERSUPLOAD
				msg.msg_type = MSGTYPE.FINISHED
				msg.adid = self.ad_id
				msg.domain_name = self.domain_name
				await self.progress_queue.put(msg)

			return True, None
			
		except Exception as e:
			logger.exception('Error while uploading memberships from file to DB')
			if self.progress_queue is not None:
				msg = GathererProgress()
				msg.type = GathererProgressType.MEMBERSUPLOAD
				msg.msg_type = MSGTYPE.ERROR
				msg.adid = self.ad_id
				msg.domain_name = self.domain_name
				msg.error = e
				await self.progress_queue.put(msg)

			return None, e
		finally:
			if self.token_file_path is not None:
				try:
					os.remove(self.token_file_path)
				except:
					pass

	async def prepare_targets(self):
		try:
			if self.resumption is True:
				self.total_targets = 1
				if self.members_target_file_handle is not None:
					raise Exception('Resumption doesnt use the target file handle!') 
				
				self.members_target_file_handle = gzip.GzipFile('member_targets.gz','wb')
				await self.generate_member_targets()

			else:
				self.members_target_file_handle.seek(0,0)
				for line in self.members_target_file_handle:
					self.total_members_to_poll += 1

			return True, None
		
		except Exception as err:
			logger.exception('prep targets')
			return False, err

	async def start_jobs(self):
		self.members_target_file_handle.seek(0,0)
		for line in self.members_target_file_handle:
				line = line.strip()
				line = line.decode()
				data = json.loads(line)
				job = LDAPAgentJob(LDAPAgentCommand.MEMBERSHIPS, data)
				await self.agent_in_q.put(job)

	async def run(self):
		try:
			adinfo = self.session.query(ADInfo).get(self.ad_id)
			self.domain_name = str(adinfo.distinguishedName).replace(',','.').replace('DC=','')
			qs = self.agent_cnt
			self.agent_in_q = asyncio.Queue(qs)
			self.agent_out_q = asyncio.Queue(qs*40)

			self.token_file_path = 'token_' + datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S") + '.gzip'
			self.token_file = gzip.GzipFile(self.token_file_path, 'w')	

			logger.debug('Polling members')
			_, res = await self.prepare_targets()
			if res is not None:
				raise res
			
			for _ in range(self.agent_cnt):
				agent = LDAPGathererAgent(self.ldap_mgr, self.agent_in_q, self.agent_out_q)
				self.agents.append(asyncio.create_task(agent.arun()))

			
			asyncio.create_task(self.start_jobs())
			if self.progress_queue is None:
				self.member_progress = tqdm(desc='Collecting members', total=self.total_members_to_poll, position=0, leave=True)
			else:
				msg = GathererProgress()
				msg.type = GathererProgressType.MEMBERS
				msg.msg_type = MSGTYPE.STARTED
				msg.adid = self.ad_id
				msg.domain_name = self.domain_name
				await self.progress_queue.put(msg)
				await asyncio.sleep(0)

			acnt = self.total_members_to_poll
			last_stat_cnt = 0
			while acnt > 0:
				try:
					res = await self.agent_out_q.get()
					res_type, res = res
						
					if res_type == LDAPAgentCommand.MEMBERSHIP:
						self.member_finish_ctr += 1
						res.ad_id = self.ad_id
						res.graph_id = self.graph_id
						self.token_file.write(res.to_json().encode() + b'\r\n')
						await asyncio.sleep(0)
					
					elif res_type == LDAPAgentCommand.MEMBERSHIP_FINISHED:
						if self.show_progress is True:
							self.member_progress.update()
						
						if acnt % self.progress_step_size == 0 and self.progress_queue is not None:
							last_stat_cnt += self.progress_step_size
							now = datetime.datetime.utcnow()
							td = (now - self.progress_last_updated).total_seconds()
							self.progress_last_updated = now
							msg = GathererProgress()
							msg.type = GathererProgressType.MEMBERS
							msg.msg_type = MSGTYPE.PROGRESS
							msg.adid = self.ad_id
							msg.domain_name = self.domain_name
							msg.total = self.total_members_to_poll
							msg.total_finished = self.total_members_to_poll - acnt
							if td > 0:
								msg.speed = str(self.progress_step_size // td)
							msg.step_size = self.progress_step_size
							await self.progress_queue.put(msg)
						acnt -= 1

					elif res_type == LDAPAgentCommand.EXCEPTION:
						logger.warning(str(res))
						
				except Exception as e:
					logger.exception('Members enumeration error!')
					raise e
			
			
			if self.progress_queue is not None:
				now = datetime.datetime.utcnow()
				td = (now - self.progress_last_updated).total_seconds()
				self.progress_last_updated = now
				msg = GathererProgress()
				msg.type = GathererProgressType.MEMBERS
				msg.msg_type = MSGTYPE.PROGRESS
				msg.adid = self.ad_id
				msg.domain_name = self.domain_name
				msg.total = self.total_members_to_poll
				msg.total_finished = self.total_members_to_poll
				if td > 0:
					msg.speed = str((self.total_members_to_poll - last_stat_cnt) // td)
				msg.step_size = (self.total_members_to_poll - last_stat_cnt)
				await self.progress_queue.put(msg)


			await self.stop_memberships_collection()

			adinfo = self.session.query(ADInfo).get(self.ad_id)
			adinfo.ldap_members_finished = True
			self.session.commit()

			return True, None
		except Exception as e:
			logger.exception('Members enumeration error main!')
			await self.stop_memberships_collection()
			return False, e
		
		finally:
			try:
				self.session.close()
			except:
				pass
