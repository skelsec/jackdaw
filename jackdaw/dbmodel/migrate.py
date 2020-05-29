

#from .addacl import *
from .adgroup import *
from .adcomp import *
from .adinfo import *
from .aduser import *
from .adou import *
from .credential import *
from .hashentry import *
from .netsession import *
from .netshare import *
from .spnservice import *
from .tokengroup import *
from .localgroup import *
from .constrained import *
from .customrelations import *
from .smbfinger import *
from .adgplink import *
from .adgpo import *
from .netfile import *
from .netdir import *
from .adsd import *
from .adtrust import *
from .lsasecrets import *
from .adspn import *

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import make_transient
from tqdm import tqdm
from sqlalchemy import func

objs_to_migrate = {
	JackDawTokenGroup : 'tokengroup',
	JackDawADUser : 'user',
	JackDawADMachine : 'machine',
	JackDawADGroup : 'group',
	JackDawADGPO : 'gpo',
	JackDawADGplink : 'gplink',
	JackDawADOU : 'ou',
	JackDawSPN : 'spn',
	JackDawADTrust : 'trust',
	JackDawMachineConstrainedDelegation : 'constraineddelegation',
	Credential : 'credential',
	JackDawCustomRelations : 'customrelation',
	LocalGroup : 'localgroup',
	LSASecret : 'secret',
	NetSession : 'session',
	NetShare : 'share',
	SMBFinger : 'smbfinger',
	JackDawSPNService : 'spnservice',
	JackDawSD : 'sd',
}
special_obj_to_migrate = {
		HashEntry : 'hash',
}
objs_to_migrate_inv = {v: k for k, v in objs_to_migrate.items()}

def windowed_query(q, column, windowsize, is_single_entity = True):
	""""Break a Query into chunks on a given column."""

	#single_entity = q.is_single_entity
	q = q.add_column(column).order_by(column)
	last_id = None

	while True:
		subq = q
		if last_id is not None:
			subq = subq.filter(column > last_id)
		chunk = subq.limit(windowsize).all()
		if not chunk:
			break
		last_id = chunk[-1][-1]
		for row in chunk:
			if is_single_entity is True:
				yield row[0]
			else:
				yield row[0:-1]

def get_session(connection, verbosity = 0):
	engine = create_engine(connection, echo=True if verbosity > 1 else False) #'sqlite:///dump.db'	
	# create a configured "Session" class
	Session = sessionmaker(bind=engine)
	# create a Session
	return Session()


def migrate_adifo(session_old, session_new, adifo):
	new_adinfo = JackDawADInfo.from_dict(adifo.to_dict())
	new_adinfo.id = None
	session_new.add(new_adinfo)
	session_new.commit()
	session_new.refresh(new_adinfo)
	return new_adinfo.id

def migrate_obj(session_old, session_new, ad_id_old, ad_id_new, obj, batch_size = 10000):
	total = session_old.query(func.count(obj.id)).filter_by(ad_id = ad_id_old).scalar()
	desc = '[+] Migrating: %s' % objs_to_migrate[obj]
	stat = tqdm(desc = desc,total=total)

	q = session_old.query(obj).filter_by(ad_id = ad_id_old)
	try:
		for i, res in enumerate(windowed_query(q, obj.id, windowsize = batch_size)):
			session_old.expunge(res)
			make_transient(res)
			res.id = None
			res.ad_id = ad_id_new
			#if isinstance(res, JackDawADUser):
			#	res.allowedtodelegateto = []
			session_new.add(res)
			stat.update()
			if i % batch_size == 0:
				session_new.flush()
				session_new.commit()
		session_new.commit()
	except Exception as e:
		print('Migration of table %s failed! Reason: %s' % ( objs_to_migrate[obj], str(e) ) )
	stat.refresh()
	stat.disable = True


def migrate(session_old, session_new):
	for res in session_old.query(JackDawADInfo).all():
		ad_id_old = res.id
		ad_id_new = migrate_adifo(session_old, session_new, res)
		for obj in objs_to_migrate:
			migrate_obj(session_old, session_new, ad_id_old, ad_id_new, obj)

def migrate_partial(session_old, session_new, ad_id_old, ad_id_new, tables):
	for table in tables:
		obj = objs_to_migrate_inv[table]
		migrate_obj(session_old, session_new, ad_id_old, ad_id_new, obj)



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
		migrate(session_old, session_new)
	elif args.command == 'partial':
		migrate_partial(session_old, session_new, args.ad_old, args.ad_new, args.tables)


if __name__ == '__main__':
	main()
	
	
	