
from jackdaw.dbmodel.tokengroup import JackDawTokenGroup
from jackdaw.nest.graph.sdcalc import SDEgdeCalc
import logging
from jackdaw import logger
from jackdaw.dbmodel import get_session, windowed_query
from jackdaw.dbmodel.spnservice import SPNService
from jackdaw.dbmodel.addacl import JackDawADDACL
from jackdaw.dbmodel.adsd import JackDawSD
from jackdaw.dbmodel.adgroup import Group
from jackdaw.dbmodel.adinfo import ADInfo
from jackdaw.dbmodel.aduser import ADUser
from jackdaw.dbmodel.adcomp import Machine
from jackdaw.dbmodel.adou import ADOU
from jackdaw.dbmodel.adinfo import ADInfo
from jackdaw.dbmodel.adtrust import ADTrust
from jackdaw.dbmodel.tokengroup import JackDawTokenGroup
from jackdaw.dbmodel.adgpo import GPO
from jackdaw.dbmodel.constrained import MachineConstrainedDelegation, JackDawUserConstrainedDelegation
from jackdaw.dbmodel.adgplink import Gplink
from jackdaw.dbmodel.adspn import JackDawSPN
from jackdaw.dbmodel.edge import Edge
from jackdaw.dbmodel.edgelookup import EdgeLookup
from jackdaw.dbmodel.netsession import NetSession
from jackdaw.dbmodel.localgroup import LocalGroup
from jackdaw.dbmodel.credential import Credential
from tqdm import tqdm

from gzip import GzipFile
from sqlalchemy import func

class EdgeCalcProgress:
	def __init__(self, status, module, current_cnt = 0, total_count = 0, speed = 0):
		self.progress_type = 'EDGECALC'
		self.status = status
		self.module = module
		self.current_cnt = current_cnt
		self.total_count = total_count
		self.speed = speed

class UniQueDict:
	def __init__(self):
		self.lookup = {}
		self.cnt = 0

	def insert(self, data):
		if data in self.lookup:
			return self.lookup[data]
		t = self.cnt
		self.lookup[data] = self.cnt
		self.cnt += 1
		return t

class EdgeCalc:
	def __init__(self, session, ad_id, output_file_dir, buffer_size = 100, dst_ad_id = None, show_progress = False, progress_queue = None, append_to_file = False, worker_count = None):
		self.session = session
		self.ad_id = ad_id
		self.output_file_dir = output_file_dir
		self.buffer_size = buffer_size
		self.dst_ad_id = dst_ad_id
		# self.dst_ad_id is for migration purposes
		if self.dst_ad_id is None:
			self.dst_ad_id = self.ad_id
		self.show_progress = show_progress
		self.progress_queue = progress_queue
		self.pbar = None

		self.total_edges = 0
		self.out_file = None
		self.append_to_file = append_to_file
		self.worker_count = worker_count

		self.lookup = UniQueDict()

	def add_edge(self, src_sid, dst_sid, label):
		self.total_edges += 1


		src_id = self.session.query(EdgeLookup.id).filter_by(oid = src_sid).filter(EdgeLookup.ad_id == self.ad_id).first()
		if src_id is None:
			#this should not happen
			t = EdgeLookup(self.ad_id, src_sid, 'unknown')
			self.session.add(t)
			self.session.commit()
			self.session.refresh(t)
			src_id = t.id
		else:
			src_id = src_id[0]
					
		dst_id = self.session.query(EdgeLookup.id).filter_by(oid = dst_sid).filter(EdgeLookup.ad_id == self.ad_id).first()
		if dst_id is None:
			#this should not happen
			t = EdgeLookup(self.ad_id, dst_sid, 'unknown')
			self.session.add(t)
			self.session.commit()
			self.session.refresh(t)
			dst_id = t.id
		else:
			dst_id = dst_id[0]

		edge = Edge(self.ad_id, src_id, dst_id, label)
		self.session.add(edge)

		#self.out_file.write( ('%s,%s,%s,%s\r\n' % (src_sid, dst_sid, label, self.dst_ad_id)).encode())

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
		for res in self.session.query(ADUser.objectSid, Machine.objectSid)\
			.filter(NetSession.username == ADUser.sAMAccountName)\
			.filter(func.lower(NetSession.source) == func.lower(Machine.dNSHostName))\
			.distinct(NetSession.username).all():
			
			self.add_edge(res[0], res[1],'hasSession')
			self.add_edge(res[1], res[0],'hasSession')
			cnt += 2
		#for machine account sessions
		for res in self.session.query(Machine.objectSid, Machine.objectSid)\
			.filter(NetSession.username == Machine.sAMAccountName)\
			.filter(func.lower(NetSession.source) == func.lower(Machine.dNSHostName))\
			.distinct(NetSession.username).all():
			
			self.add_edge(res[0], res[1],'hasSession')
			self.add_edge(res[1], res[0],'hasSession')
			cnt += 2
		logger.debug('Added %s hassession edges' % cnt)

	def localgroup_edges(self):
		logger.debug('Adding localgroup edges')
		cnt = 0
		for res in self.session.query(ADUser.objectSid, Machine.objectSid, LocalGroup.groupname
					).filter(Machine.objectSid == LocalGroup.machine_sid
					).filter(Machine.ad_id == self.ad_id
					).filter(ADUser.ad_id == self.ad_id
					).filter(ADUser.objectSid == LocalGroup.sid
					).all():
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
					
			self.add_edge(res[0], res[1], label)
			cnt += 1

		logger.debug('Added %s localgroup edges' % cnt)

	def passwordsharing_edges(self):
		logger.info('Adding password sharing edges')
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

		logger.info('Added %s password sharing edges' % cnt)

	def gplink_edges(self):
		logger.info('Adding gplink edges')
		q = self.session.query(ADOU.objectGUID, GPO.objectGUID)\
				.filter_by(ad_id = self.ad_id)\
				.filter(ADOU.objectGUID == Gplink.ou_guid)\
				.filter(Gplink.gpo_dn == GPO.cn)
		cnt = 0
		for res in q.all():
				self.add_edge(res[0], res[1], 'gplink')
				cnt += 1
		logger.info('Added %s gplink edges' % cnt)

	def groupmembership_edges(self):
		return
		#logger.info('Adding groupmembership edges')
		#q = self.session.query(JackDawTokenGroup).filter_by(ad_id = self.ad_id)
		#cnt = 0
		#for _, res in enumerate(windowed_query(q, JackDawTokenGroup.id, windowsize = self.buffer_size)):
		#		self.add_edge(res.sid, res.member_sid, 'member')
		#		cnt += 1
		#logger.info('Added %s groupmembership edges' % cnt)

	def run(self):
		try:
			if self.append_to_file is True:
				mode = 'ab+'
			else:
				mode = 'wb'
			
			output_file_path = self.output_file_dir.joinpath('temp_edges.gz')
			self.out_file = GzipFile(output_file_path,mode)
			self.gplink_edges()
			self.groupmembership_edges()
			self.trust_edges()
			self.sqladmin_edges()
			self.hasession_edges()
			self.localgroup_edges()
			self.passwordsharing_edges()
			self.out_file.close()
			sdcalc = SDEgdeCalc(
				self.session, 
				self.ad_id, 
				output_file_path, 
				worker_count = self.worker_count, 
				buffer_size = self.buffer_size, 
				append_to_file = True
			)
			sdcalc.run()

			#output_file_path_final = self.output_file_dir.joinpath('edges.gz')
			#with GzipFile(output_file_path_final,'wb') as o:
			#	with GzipFile(output_file_path,'rb') as f:
			#		for line in f:
			#			line = line.strip()
			#			line = line.decode()
			#			src, dst, *rest = line.split(',')
			#			t = ','.join(rest)
			#			src = self.lookup.insert(src)
			#			dst = self.lookup.insert(dst)
			#			o.write( ('%s,%s,%s\r\n' % (src,dst,t)).encode())
			#
			#output_file_path_maps = self.output_file_dir.joinpath('maps.gz')
			#with GzipFile(output_file_path_maps,'wb') as o:
			#	for k in self.lookup.lookup:
			#		o.write(('%s,%s\r\n' % (k, self.lookup.lookup[k])).encode())

			output_file_path.unlink()

		except Exception as e:
			logger.exception('edge calculation error!')

		finally:
			try:
				if self.out_file is not None:
					self.out_file.close()
			except:
				pass
		print('Done!')

def main():
	import argparse
	parser = argparse.ArgumentParser(description='Calculate edges and flattem them in a file')
	parser.add_argument('-v', '--verbose', action='count', default=0, help='Increase verbosity, can be stacked')

	subparsers = parser.add_subparsers(help = 'dunno')
	subparsers.required = True
	subparsers.dest = 'command'

	full_group = subparsers.add_parser('run', help='Full migration')
	full_group.add_argument('sql',  help='SQL connection string.')
	full_group.add_argument('ad', type=int, help='AD id to calc the edges on')
	full_group.add_argument('outfile', help='output file path')
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

	session = get_session(args.sql)

	if args.command == 'run':
		calc = EdgeCalc(session, args.ad, args.outfile, buffer_size = 100, dst_ad_id = None, worker_count = args.worker_count)
		calc.run()
	
	else:
		print('?????')

if __name__ == '__main__':
	main()