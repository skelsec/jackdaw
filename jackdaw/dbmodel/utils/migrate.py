

from jackdaw.dbmodel.adgroup import *
from jackdaw.dbmodel.adcomp import *
from jackdaw.dbmodel.adinfo import *
from jackdaw.dbmodel.aduser import *
from jackdaw.dbmodel.adou import *
from jackdaw.dbmodel.credential import *
from jackdaw.dbmodel.hashentry import *
from jackdaw.dbmodel.netsession import *
from jackdaw.dbmodel.netshare import *
from jackdaw.dbmodel.spnservice import *
from jackdaw.dbmodel.localgroup import *
from jackdaw.dbmodel.constrained import *
from jackdaw.dbmodel.smbfinger import *
from jackdaw.dbmodel.adgplink import *
from jackdaw.dbmodel.adgpo import *
from jackdaw.dbmodel.netfile import *
from jackdaw.dbmodel.netdir import *
from jackdaw.dbmodel.adsd import *
from jackdaw.dbmodel.adtrust import *
from jackdaw.dbmodel.lsasecrets import *
from jackdaw.dbmodel.adspn import *
from jackdaw.dbmodel.neterror import NetError
from jackdaw.dbmodel.rdnslookup import RDNSLookup
from jackdaw.dbmodel.adobjprops import ADObjProps
from jackdaw.dbmodel import windowed_query

from jackdaw.dbmodel.edgelookup import EdgeLookup
from jackdaw.dbmodel.edge import Edge
from jackdaw.dbmodel.graphinfo import GraphInfo

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import make_transient
from tqdm import tqdm
from sqlalchemy import func
from jackdaw.utils.encoder import UniversalEncoder
import pathlib
from sqlalchemy.inspection import inspect
import os
import datetime

# NetDACL
# NetDir
# NetFile

objs_to_migrate = {
	ADUser : 'user',
	Machine : 'machine',
	Group : 'group',
	GPO : 'gpo',
	Gplink : 'gplink',
	ADOU : 'ou',
	JackDawSPN : 'spn',
	ADTrust : 'trust',
	MachineConstrainedDelegation : 'constraineddelegation',
	Credential : 'credential',
	LocalGroup : 'localgroup',
	LSASecret : 'secret',
	NetSession : 'session',
	NetShare : 'share',
	SMBFinger : 'smbfinger',
	SPNService : 'spnservice',
	JackDawSD : 'sd',
	EdgeLookup : 'edgelookup',
	ADObjProps : 'objprops',
	RDNSLookup : 'rdns',
	NetError : 'neterr',
}

objs_to_migrate_inv = {v: k for k, v in objs_to_migrate.items()}

class Migrator:
	def __init__(self, session_old, session_new, work_dir = None, batch_size = 1000):
		self.session_old = session_old
		self.session_new = session_new
		self.batch_size = batch_size

		self.work_dir = work_dir
		if self.work_dir is None:
			self.work_dir = pathlib.Path('./workdir')
		elif isinstance(self.work_dir, str):
			self.work_dir = pathlib.Path(self.work_dir)

		base = '%s_%s' % (datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S"), os.urandom(4).hex())
		self.work_dir = self.work_dir.joinpath('migration').joinpath(base)
		self.work_dir.mkdir(parents=True, exist_ok=False)

		self.edge_lookup = {}


	def migrate_adifo(self,adifo):
		new_adinfo = ADInfo.from_dict(adifo.to_dict())
		new_adinfo.id = None
		self.session_new.add(new_adinfo)
		self.session_new.commit()
		self.session_new.refresh(new_adinfo)
		return new_adinfo.id


	def migrate(self):
		self.migrate_hashes()
		for res in self.session_old.query(ADInfo).all():
			ad_id_old = res.id
			ad_id_new = self.migrate_adifo(res)
			for i, obj in enumerate(objs_to_migrate):
				self.migrate_table(ad_id_old, ad_id_new, obj, i)
			self.migrate_graphdata(ad_id_old, ad_id_new)

		self.session_new.commit()

	def migrate_hashes(self):
		try:
			filename = '%s_%s.json' % ('hashes', 'none')
			filepath = self.work_dir.joinpath(filename)
			total = self.session_old.query(func.count(HashEntry.id)).scalar()
			desc = '[+] Dumping %s table to file (%s)->(%s)' % ('hashes', 'na', 'na')
			stat = tqdm(desc = desc,total=total)

			with open(str(filepath), 'w', newline = '') as f:
				q = self.session_old.query(HashEntry)
				try:
					for i, res in enumerate(windowed_query(q, HashEntry.id, windowsize = self.batch_size)):
						stat.update()
						self.session_old.expunge(res)
						make_transient(res)
						res.id = None

						f.write(json.dumps(HashEntry.serialize(res), cls = UniversalEncoder) + '\r\n')
						if i % self.batch_size == 0:
							f.flush()

				except Exception as e:
					print('Migration of table %s failed! Reason: %s' % ( 'HashEntry', str(e) ) )

			stat.refresh()
			stat.disable = True

			desc = '[+] Loading %s table file to new DB (%s)->(%s)' % ('HashEntry','na', 'na')
			stat = tqdm(desc = desc,total=total)
			with open(str(filepath), 'r') as f:
				for line in f:
					line = line.strip()
					if line == '':
						continue

					dd = json.loads(line)
					### this part is here because some fields require datetime format. but we dont know which ones
					
					for x in inspect(HashEntry).columns:
						if str(x.type) == 'DATETIME' and dd[x.name] is not None:
								dd[x.name] = datetime.datetime.fromisoformat(dd[x.name])

					del dd['id']
					hash_entry = HashEntry(**dd)
					stat.update()

					if hash_entry.nt_hash is not None:
						res = self.session_new.query(HashEntry).filter_by(nt_hash = hash_entry.nt_hash).first()
						if res is not None:
							continue
						self.session_new.add(hash_entry)
						self.session_new.commit()
						continue

					elif hash_entry.lm_hash is not None:
						res = self.session_new.query(HashEntry).filter_by(lm_hash = hash_entry.lm_hash).first()
						if res is not None:
							continue
						self.session_new.add(hash_entry)
						self.session_new.commit()
						continue
					
			stat.refresh()
			stat.disable = True

		except Exception as e:
			print(e)
		finally:
			try:
				os.unlink(str(filepath))
			except:
				pass


	def migrate_table(self, ad_id_old, ad_id_new, obj, prog_pos):
		try:
			filename = '%s_%s.json' % (objs_to_migrate[obj], ad_id_new)
			filepath = self.work_dir.joinpath(filename)
			total = self.session_old.query(func.count(obj.id)).filter_by(ad_id = ad_id_old).scalar()
			desc = '[+] Dumping %s table to file (%s)->(%s)' % (objs_to_migrate[obj], ad_id_old, ad_id_new)
			stat = tqdm(desc = desc,total=total, position=prog_pos)

			
			with open(str(filepath), 'w', newline = '') as f:
				q = self.session_old.query(obj).filter_by(ad_id = ad_id_old)
				try:
					for i, res in enumerate(windowed_query(q, obj.id, windowsize = self.batch_size)):
						stat.update()
						self.session_old.expunge(res)
						make_transient(res)
						res.id = None
						res.ad_id = ad_id_new

						f.write(json.dumps(obj.serialize(res), cls = UniversalEncoder) + '\r\n')
						if i % self.batch_size == 0:
							f.flush()

				except Exception as e:
					print('Migration of table %s failed! Reason: %s' % ( objs_to_migrate[obj], str(e) ) )
			stat.refresh()
			stat.disable = True

			desc = '[+] Loading %s table file to new DB (%s)->(%s)' % (objs_to_migrate[obj], ad_id_old, ad_id_new)
			stat = tqdm(desc = desc,total=total, position=prog_pos)
			with open(str(filepath), 'r') as f:
				for line in f:
					line = line.strip()
					if line == '':
						continue

					dd = json.loads(line)
					### this part is here because some fields require datetime format. but we dont know which ones
					
					for x in inspect(obj).columns:
						if str(x.type) == 'DATETIME' and dd[x.name] is not None:
								dd[x.name] = datetime.datetime.fromisoformat(dd[x.name])

					del dd['id']
					dbobj = obj(**dd)
					self.session_new.add(dbobj)
					stat.update()
					if i % self.batch_size == 0:
						self.session_new.commit()
			stat.refresh()
			stat.disable = True
		
		except Exception as e:
			print('err! %s' % str(e))
		finally:
			try:
				os.unlink(str(filepath))
			except:
				pass


	def __get_edge_remap(self, ad_id_new, lid):
		if lid in self.edge_lookup:
			return self.edge_lookup[lid]
		old_src = self.session_old.query(EdgeLookup).get(lid)
		new_src = self.session_new.query(EdgeLookup.id).filter_by(ad_id = ad_id_new).filter(EdgeLookup.oid == old_src.oid).first()

		self.edge_lookup[lid] = new_src[0]
		
		return new_src[0]

	def migrate_graphdata(self, ad_id_old, ad_id_new):
		for graphinfo in self.session_old.query(GraphInfo).filter_by(ad_id = ad_id_old).all():
			old_graph_id = graphinfo.id
			self.session_old.expunge(graphinfo)
			make_transient(graphinfo)
			graphinfo.id = None
			graphinfo.ad_id = ad_id_new
			self.session_new.add(graphinfo)
			self.session_new.commit()
			self.session_new.refresh(graphinfo)
			
			batch_size = 10000
			total = self.session_old.query(func.count(Edge.id)).filter_by(graph_id = old_graph_id).scalar()
			desc = '[+] Migrating edges for graphid %s' % old_graph_id
			stat = tqdm(desc = desc,total=total)
			q = self.session_old.query(Edge).filter_by(graph_id = old_graph_id)
			for i, edge in enumerate(windowed_query(q, Edge.id, windowsize = batch_size)):
				new_src = self.__get_edge_remap(ad_id_new, edge.src)
				new_dst = self.__get_edge_remap(ad_id_new, edge.dst)
				
				newedge = Edge(ad_id_new, graphinfo.id, new_src, new_dst, edge.label)
				self.session_new.add(newedge)
				if i % batch_size == 0:
					stat.update(batch_size)
					self.session_new.commit()


def get_session(connection, verbosity = 0):
	engine = create_engine(connection, echo=True if verbosity > 1 else False) #'sqlite:///dump.db'	
	# create a configured "Session" class
	Session = sessionmaker(bind=engine)
	# create a Session
	return Session()



def main():
	import argparse
	parser = argparse.ArgumentParser(description='Gather gather gather')
	parser.add_argument('-v', '--verbose', action='count', default=0, help='Increase verbosity, can be stacked')

	subparsers = parser.add_subparsers(help = 'migration type')
	subparsers.required = True
	subparsers.dest = 'command'

	full_group = subparsers.add_parser('full', help='Full migration')
	full_group.add_argument('old',  help='SQL connection string.')
	full_group.add_argument('new',  help='SQL connection string.')

	partial_group = subparsers.add_parser('partial', help='Full migration')
	partial_group.add_argument('old',  help='SQL connection string.')
	partial_group.add_argument('new',  help='SQL connection string.')
	partial_group.add_argument('ad_old', help='ID of the old domainfo')
	partial_group.add_argument('ad_new', help='ID of the new domainfo')
	partial_group.add_argument('tables',  nargs='+', help='Table names to migrate')

	args = parser.parse_args()

	session_old = get_session(args.old)
	session_new = get_session(args.new)

	if args.command == 'full':
		m = Migrator(session_old, session_new)
		m.migrate()


if __name__ == '__main__':
	main()
	
	
	