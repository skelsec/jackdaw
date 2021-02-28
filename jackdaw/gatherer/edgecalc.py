
import os
import asyncio
import logging
import datetime
import tempfile
import platform
import pathlib

try:
	import multiprocessing as mp
except ImportError:
	mp = None

from jackdaw import logger
from jackdaw.dbmodel import get_session, windowed_query
from jackdaw.dbmodel.spnservice import SPNService
from jackdaw.dbmodel.adsd import JackDawSD
from jackdaw.dbmodel.adgroup import Group
from jackdaw.dbmodel.adinfo import ADInfo
from jackdaw.dbmodel.aduser import ADUser
from jackdaw.dbmodel.adcomp import Machine
from jackdaw.dbmodel.adou import ADOU
from jackdaw.dbmodel.adinfo import ADInfo
from jackdaw.dbmodel.adtrust import ADTrust
from jackdaw.dbmodel.adgpo import GPO
from jackdaw.dbmodel.constrained import MachineConstrainedDelegation
from jackdaw.dbmodel.adallowedtoact import MachineAllowedToAct
from jackdaw.dbmodel.adgplink import Gplink
from jackdaw.dbmodel.adspn import JackDawSPN
from jackdaw.dbmodel.edge import Edge
from jackdaw.dbmodel.edgelookup import EdgeLookup
from jackdaw.dbmodel.netsession import NetSession
from jackdaw.dbmodel.localgroup import LocalGroup
from jackdaw.dbmodel.credential import Credential
from jackdaw.dbmodel.graphinfo import GraphInfo, GraphInfoAD
from jackdaw.gatherer.sdcalc import calc_sd_edges

from sqlalchemy.orm.session import make_transient
from tqdm import tqdm
from jackdaw.gatherer.progress import *

from sqlalchemy import func

class EdgeCalcProgress:
	def __init__(self, status, module, current_cnt = 0, total_count = 0, speed = 0):
		self.progress_type = 'EDGECALC'
		self.status = status
		self.module = module
		self.current_cnt = current_cnt
		self.total_count = total_count
		self.speed = speed
		

class EdgeCalc:
	def __init__(self, db_conn, ad_id, graph_id, buffer_size = 100, show_progress = True, progress_queue = None, worker_count = None, mp_pool = None, work_dir = None):
		self.db_conn = db_conn
		self.ad_id = ad_id
		self.buffer_size = buffer_size
		self.show_progress = show_progress
		self.work_dir = work_dir
		self.progress_queue = progress_queue
		self.progress_step_size = 1000
		self.pbar = None
		self.mp_pool = mp_pool
		self.graph_id = graph_id
		self.domain_name = None
		self.progress_last_updated = datetime.datetime.utcnow()
		self.disable_tqdm = True if platform.system() == 'Emscripten' else False

		self.total_edges = 0
		self.sd_edges_written = 0
		self.worker_count = worker_count
		self.boost_dict = {}
		self.session = None
		self.foreign_pool = False
		if self.mp_pool is None:
			self.foreign_pool = True

		if self.worker_count is None:
			self.worker_count = 10

	def get_id_for_sid(self, sid, otype = 'unknown', with_boost = False):
		if sid in self.boost_dict:
			return self.boost_dict[sid]
		orig = sid
		sid = self.session.query(EdgeLookup.id).filter_by(oid = sid).filter(EdgeLookup.ad_id == self.ad_id).first()
		if sid is None:
			#this should not happen
			t = EdgeLookup(self.ad_id, sid, 'unknown')
			self.session.add(t)
			self.session.commit()
			self.session.refresh(t)
			sid = t.id
		else:
			sid = sid[0]
		self.boost_dict[orig] = sid
		return sid

	def add_edge(self, src_sid, dst_sid, label, with_boost = False):
		self.total_edges += 1
		src_id = self.get_id_for_sid(src_sid, with_boost = with_boost)		
		dst_id = self.get_id_for_sid(dst_sid, with_boost = with_boost)

		edge = Edge(self.ad_id, self.graph_id, src_id, dst_id, label)
		self.session.add(edge)
		if self.total_edges % 10000 == 0:
			self.session.commit()

	async def log_msg(self, text):
		if self.progress_queue is not None:
			msg = GathererProgress()
			msg.type = GathererProgressType.INFO
			msg.msg_type = MSGTYPE.FINISHED
			msg.adid = self.ad_id
			msg.domain_name = self.domain_name
			msg.text = text
			await self.progress_queue.put(msg)

	def trust_edges(self):
		logger.debug('Adding trusts edges')
		cnt = 0
		adinfo = self.session.query(ADInfo).get(self.ad_id)
		for trust in self.session.query(ADTrust).filter_by(ad_id = self.ad_id):
			if trust.trustDirection == 'INBOUND':
				self.add_edge(adinfo.objectSid, trust.securityIdentifier,'trustedBy')
				cnt += 1
			elif trust.trustDirection == 'OUTBOUND':
				self.add_edge(trust.securityIdentifier, adinfo.objectSid,'trustedBy')
				cnt += 1
			elif trust.trustDirection == 'BIDIRECTIONAL':
				self.add_edge(adinfo.objectSid, trust.securityIdentifier,'trustedBy')
				self.add_edge(trust.securityIdentifier, adinfo.objectSid,'trustedBy')
				cnt += 2
		
		self.total_edges += cnt
		logger.debug('Added %s trusts edges' % cnt)

	def sqladmin_edges(self):
		logger.debug('Adding sqladmin edges')
		cnt = 0
		for user_sid, machine_sid in self.session.query(JackDawSPN.owner_sid, Machine.objectSid)\
				.filter(JackDawSPN.ad_id == self.ad_id)\
				.filter(Machine.ad_id == self.ad_id)\
				.filter(ADUser.ad_id == self.ad_id)\
				.filter(JackDawSPN.owner_sid == ADUser.objectSid)\
				.filter(JackDawSPN.service_class == 'MSSQLSvc')\
				.filter(JackDawSPN.computername == Machine.dNSHostName):
			self.add_edge(user_sid, machine_sid,'sqladmin')
			cnt += 1
		logger.debug('Added %s sqladmin edges' % cnt)

	def hasession_edges(self):
		logger.debug('Adding hassession edges')
		cnt = 0
		#for user sessions
		q = self.session.query(ADUser.objectSid, Machine.objectSid)\
			.filter(NetSession.username == ADUser.sAMAccountName)\
			.filter(func.lower(NetSession.source) == func.lower(Machine.dNSHostName))\
			.distinct(NetSession.username)
		
		for res in windowed_query(q, ADUser.id, self.buffer_size, False):
			self.add_edge(res[0], res[1],'hasSession')
			self.add_edge(res[1], res[0],'hasSession')
			cnt += 2
		#for machine account sessions
		q = self.session.query(Machine.objectSid, Machine.objectSid)\
			.filter(NetSession.username == Machine.sAMAccountName)\
			.filter(func.lower(NetSession.source) == func.lower(Machine.dNSHostName))\
			.distinct(NetSession.username)

		for res in windowed_query(q, Machine.id, self.buffer_size, False):
			
			self.add_edge(res[0], res[1],'hasSession')
			self.add_edge(res[1], res[0],'hasSession')
			cnt += 2
		logger.debug('Added %s hassession edges' % cnt)

	def localgroup_edges(self):
		logger.debug('Adding localgroup edges')
		cnt = 0
		q = self.session.query(ADUser.objectSid, Machine.objectSid, LocalGroup.groupname
					).filter(Machine.objectSid == LocalGroup.machine_sid
					).filter(Machine.ad_id == self.ad_id
					).filter(ADUser.ad_id == self.ad_id
					).filter(ADUser.objectSid == LocalGroup.sid
					)
		for res in windowed_query(q, ADUser.id, self.buffer_size, False):
			label = None
			if res[2] == 'Remote Desktop Users':
				label = 'canRDP'
				weight = 1
					
			elif res[2] == 'Distributed COM Users':
				label = 'executeDCOM'
				weight = 1
					
			elif res[2] == 'Administrators':
				label = 'adminTo'
				weight = 1

			elif res[2] == 'Remote Management Users':
				label = 'psremote'
				weight = 1
					
			self.add_edge(res[0], res[1], label)
			cnt += 1

		logger.debug('Added %s localgroup edges' % cnt)

	def passwordsharing_edges(self):
		logger.debug('Adding password sharing edges')
		cnt = 0
		def get_sid_by_nthash(ad_id, nt_hash):
			return self.session.query(ADUser.objectSid, Credential.username
				).filter_by(ad_id = ad_id
				).filter(Credential.username == ADUser.sAMAccountName
				).filter(Credential.nt_hash == nt_hash
				)

		dup_nthashes_qry = self.session.query(Credential.nt_hash
					).filter(Credential.history_no == 0
					).filter(Credential.ad_id == self.ad_id
					   ).filter(Credential.username != 'NA'
					   ).filter(Credential.domain != '<LOCAL>'
					).group_by(
						Credential.nt_hash
					).having(
						func.count(Credential.nt_hash) > 1
					)

		for res in dup_nthashes_qry.all():
			sidd = {}
			for sid, _ in get_sid_by_nthash(self.ad_id, res[0]).all():
				sidd[sid] = 1

			for sid1 in sidd:
				for sid2 in sidd:
					if sid1 == sid2:
						continue
					self.add_edge(sid1, sid2,label = 'pwsharing')
					cnt += 1

		logger.debug('Added %s password sharing edges' % cnt)

	def gplink_edges(self):
		logger.debug('Adding gplink edges')
		q = self.session.query(ADOU.objectGUID, GPO.objectGUID)\
				.filter_by(ad_id = self.ad_id)\
				.filter(ADOU.objectGUID == Gplink.ou_guid)\
				.filter(Gplink.gpo_dn == GPO.cn)
		cnt = 0
		for res in windowed_query(q, GPO.id, self.buffer_size, False):
				self.add_edge(res[0], res[1], 'gplink')
				cnt += 1
		logger.debug('Added %s gplink edges' % cnt)

	def allowedtoact_edges(self):
		logger.debug('Adding allowedtoact edges')
		q = self.session.query(MachineAllowedToAct.machine_sid, MachineAllowedToAct.target_sid)\
				.filter_by(ad_id = self.ad_id)
		cnt = 0
		for res in windowed_query(q, MachineAllowedToAct.id, self.buffer_size, False):
				self.add_edge(res[1], res[0], 'allowedtoact')
				cnt += 1
		logger.debug('Added %s allowedtoact edges' % cnt)
		

	def groupmembership_edges(self):
		return
		#logger.info('Adding groupmembership edges')
		#q = self.session.query(JackDawTokenGroup).filter_by(ad_id = self.ad_id)
		#cnt = 0
		#for _, res in enumerate(windowed_query(q, JackDawTokenGroup.id, windowsize = self.buffer_size)):
		#		self.add_edge(res.sid, res.member_sid, 'member')
		#		cnt += 1
		#logger.info('Added %s groupmembership edges' % cnt)

	def calc_sds_batch(self, buffer, testfile):
		if self.mp_pool is not None:
			for res in self.mp_pool.imap_unordered(calc_sd_edges, buffer):
				for r in res:
					src,dst,label,ad_id = r
					src = self.get_id_for_sid(src, with_boost=True)
					dst = self.get_id_for_sid(dst, with_boost=True)
					self.sd_edges_written += 1
					testfile.write('%s,%s,%s,%s\r\n' % (src, dst, label, ad_id))
		else:
			#this will take forever like this...
			for adsd in buffer:
				for res in calc_sd_edges(adsd):
					src,dst,label,ad_id = res
					src = self.get_id_for_sid(src, with_boost=True)
					dst = self.get_id_for_sid(dst, with_boost=True)
					self.sd_edges_written += 1
					testfile.write('%s,%s,%s,%s\r\n' % (src, dst, label, ad_id))

	async def calc_sds_mp(self):
		await self.log_msg('Calculating SD edges')
		logger.debug('starting calc_sds_mp')
		try:
			cnt = 0
			total = self.session.query(func.count(JackDawSD.id)).filter(JackDawSD.ad_id == self.ad_id).scalar()
			logger.debug('calc_sds_mp total SDs %s' % str(total))
			q = self.session.query(JackDawSD).filter_by(ad_id = self.ad_id)

			if self.progress_queue is not None:
				msg = GathererProgress()
				msg.type = GathererProgressType.SDCALC
				msg.msg_type = MSGTYPE.STARTED
				msg.adid = self.ad_id
				msg.domain_name = self.domain_name
				await self.progress_queue.put(msg)

			sdcalc_pbar = None
			if self.show_progress is True:
				sdcalc_pbar = tqdm(desc ='Writing SD edges to file', total=total, disable=self.disable_tqdm)

			sdfilename = 'sdcalc.csv'
			if self.work_dir is not None:
				sdfilename = str(self.work_dir.joinpath('sdcalc.csv'))

			testfile = open(sdfilename, 'w+', newline = '') #tempfile.TemporaryFile('w+', newline = '')
			buffer = []
			if self.mp_pool is None:
				try:
					self.mp_pool = mp.Pool()
				except ImportError:
					self.mp_pool = None
					
			logger.debug('calc_sds_mp starting calc')
			tf = 0
			last_stat_cnt = 0
			try:
				for adsd in windowed_query(q, JackDawSD.id, self.buffer_size):
					tf += 1
					adsd = JackDawSD.from_dict(adsd.to_dict())
					buffer.append(adsd)
					if len(buffer) == self.buffer_size:
						self.calc_sds_batch(buffer, testfile)
						buffer = []
						
						if sdcalc_pbar is not None:
							sdcalc_pbar.update(self.buffer_size)
								
					if self.progress_queue is not None and tf % self.progress_step_size == 0:
						last_stat_cnt += self.progress_step_size
						now = datetime.datetime.utcnow()
						td = (now - self.progress_last_updated).total_seconds()
						self.progress_last_updated = now
						msg = GathererProgress()
						msg.type = GathererProgressType.SDCALC
						msg.msg_type = MSGTYPE.PROGRESS
						msg.adid = self.ad_id
						msg.domain_name = self.domain_name
						msg.total = total
						msg.total_finished = tf
						if td > 0:
							msg.speed = str(self.progress_step_size // td)
						msg.step_size = self.progress_step_size
						await self.progress_queue.put(msg)
						await asyncio.sleep(0)
				
				if len(buffer) > 0:
					self.calc_sds_batch(buffer, testfile)
					if self.progress_queue is not None:
						now = datetime.datetime.utcnow()
						td = (now - self.progress_last_updated).total_seconds()
						self.progress_last_updated = now
						msg = GathererProgress()
						msg.type = GathererProgressType.SDCALC
						msg.msg_type = MSGTYPE.PROGRESS
						msg.adid = self.ad_id
						msg.domain_name = self.domain_name
						msg.total = total
						msg.total_finished = tf
						if td > 0:
							msg.speed = str(len(buffer) // td)
						msg.step_size = tf - last_stat_cnt
						await self.progress_queue.put(msg)
						await asyncio.sleep(0)

					buffer = []

				if self.progress_queue is not None:
					msg = GathererProgress()
					msg.type = GathererProgressType.SDCALC
					msg.msg_type = MSGTYPE.FINISHED
					msg.adid = self.ad_id
					msg.domain_name = self.domain_name
					await self.progress_queue.put(msg)

				
				if self.show_progress is True and sdcalc_pbar is not None:
					sdcalc_pbar.refresh()
					sdcalc_pbar.disable = True

			except Exception as e:
				logger.exception('SD calc exception!')
				raise e
			finally:
				if self.foreign_pool is False and self.mp_pool is not None:
					self.mp_pool.close()

			if self.progress_queue is not None:
				msg = GathererProgress()
				msg.type = GathererProgressType.SDCALCUPLOAD
				msg.msg_type = MSGTYPE.STARTED
				msg.adid = self.ad_id
				msg.domain_name = self.domain_name
				await self.progress_queue.put(msg)
			
			logger.debug('Writing SD edge file contents to DB')
			await self.log_msg('Writing SD edge file contents to DB')
			sdcalcupload_pbar = None
			if self.show_progress is True:
				sdcalcupload_pbar = tqdm(desc = 'Writing SD edge file contents to DB', total = cnt, disable=self.disable_tqdm)

			engine = self.session.get_bind()
			print(engine)

			testfile.seek(0,0)
			last_stat_cnt = 0
			i = 0

			insert_buffer = []
			for line in testfile:
				i += 1
				line = line.strip()
				src_id, dst_id, label, _ = line.split(',')
				insert_buffer.append(
					{
						"ad_id": self.ad_id,
						'graph_id' : self.graph_id,
						'src' : int(src_id),
						'dst' : int(dst_id),
						'label' : label
					}
				)
				if i % (self.buffer_size*100) == 0:
					engine.execute(Edge.__table__.insert(), insert_buffer)
					if self.show_progress is True:
						sdcalcupload_pbar.update(self.buffer_size*100)
					insert_buffer = []
					
				if self.progress_queue is not None and i % self.progress_step_size == 0:
					last_stat_cnt += self.progress_step_size
					now = datetime.datetime.utcnow()
					td = (now - self.progress_last_updated).total_seconds()
					self.progress_last_updated = now
					msg = GathererProgress()
					msg.type = GathererProgressType.SDCALCUPLOAD
					msg.msg_type = MSGTYPE.PROGRESS
					msg.adid = self.ad_id
					msg.domain_name = self.domain_name
					msg.total = self.sd_edges_written
					msg.total_finished = i
					if td > 0:
						msg.speed = str(self.progress_step_size // td)
					msg.step_size = self.progress_step_size
					await self.progress_queue.put(msg)
					await asyncio.sleep(0)
			
			if len(insert_buffer) > 0:
				engine.execute(Edge.__table__.insert(), insert_buffer)
				if self.show_progress is True:
					sdcalcupload_pbar.update(len(insert_buffer))
				insert_buffer = []

			if self.progress_queue is not None:
				msg = GathererProgress()
				msg.type = GathererProgressType.SDCALCUPLOAD
				msg.msg_type = MSGTYPE.FINISHED
				msg.adid = self.ad_id
				msg.domain_name = self.domain_name
				await self.progress_queue.put(msg)
			
			self.session.commit()
			return True, None
		except Exception as e:
			logger.exception('sdcalc!')
			return False, e
		finally:
			os.remove(sdfilename)
			
		

	async def start_calc(self):
		#call this only after setting the current ADID!!!!
		try:
			if self.work_dir is not None:
				if isinstance(self.work_dir, str):
					self.work_dir = pathlib.Path(self.work_dir)

			adinfo = self.session.query(ADInfo).get(self.ad_id)
			self.domain_name = str(adinfo.distinguishedName).replace(',','.').replace('DC=','')
			

			await self.log_msg('Adding gplink edges')
			self.gplink_edges()
			#await self.log_msg()
			#self.groupmembership_edges()
			await self.log_msg('Adding trusts edges')
			self.trust_edges()
			await self.log_msg('Adding sqladmin edges')
			self.sqladmin_edges()
			await self.log_msg('Adding hassession edges')
			self.hasession_edges()
			await self.log_msg('Adding localgroup edges')
			self.localgroup_edges()
			await self.log_msg('Adding password sharing edges')
			self.passwordsharing_edges()
			await self.log_msg('Adding allowedtoact sharing edges')
			self.allowedtoact_edges()
			self.session.commit()
			_, err = await self.calc_sds_mp()
			if err is not None:
				raise err
			
			adinfo = self.session.query(ADInfo).get(self.ad_id)
			adinfo.edges_finished = True
			self.session.commit()
			return True, None
		except Exception as e:
			logger.exception('edge calculation error!')
			return False, e

	async def run(self):
		try:
			self.session = get_session(self.db_conn)
			if self.ad_id is None and self.graph_id is not None:
				#recalc!
				self.session.query(Edge).filter_by(graph_id = self.graph_id).filter(Edge.label != 'member').delete()
				self.session.commit()

				res = self.session.query(GraphInfo).get(self.graph_id)
				for giad in self.session.query(GraphInfoAD).filter_by(graph_id = self.graph_id).all():
					self.ad_id = giad.ad_id
					_, err = await self.start_calc()
					if err is not None:
						raise err

			else:
				_, err = await self.start_calc()
				if err is not None:
					raise err
			
			return True, None

		except Exception as e:
			logger.exception('edge calculation error!')
			return False, e
		finally:
			try:
				self.session.close()
			except:
				pass

def main():
	import argparse
	import os
	parser = argparse.ArgumentParser(description='Calculate edges and flattem them in a file')
	parser.add_argument('-v', '--verbose', action='count', default=0, help='Increase verbosity, can be stacked')

	subparsers = parser.add_subparsers(help = 'dunno')
	subparsers.required = True
	subparsers.dest = 'command'

	full_group = subparsers.add_parser('run', help='Full migration')
	full_group.add_argument('sql',  help='SQL connection string.')
	full_group.add_argument('ad', type=int, help='AD id to calc the edges on')
	full_group.add_argument('-g','--graph-id', type=int, default = -1, help='AD id to calc the edges on')
	full_group.add_argument('-w', '--worker-count', type=int, default = 4,  help='output file path')

	args = parser.parse_args()

	if args.verbose == 0:
		logging.basicConfig(level=logging.INFO)
		logger.setLevel(logging.INFO)
		
	elif args.verbose == 1:
		logging.basicConfig(level=logging.DEBUG)
		logger.setLevel(logging.DEBUG)
		
	elif args.verbose > 1:
		logging.basicConfig(level=1)
		logger.setLevel(1)

	os.environ['JACKDAW_SQLITE'] = '0'
	if args.sql.lower().startswith('sqlite'):
		os.environ['JACKDAW_SQLITE'] = '1'

	session = get_session(args.sql)

	graph_id = args.graph_id
	if graph_id == -1:
		gi = GraphInfo()
		session.add(gi)
		session.commit()
		session.refresh(gi)
		graph_id = gi.id

	if args.command == 'run':
		calc = EdgeCalc(session, args.ad, graph_id, buffer_size = 100, worker_count = args.worker_count)
		calc.run()
	
	else:
		print('?????')

if __name__ == '__main__':
	main()