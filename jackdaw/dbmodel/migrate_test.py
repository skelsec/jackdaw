

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

objs_to_migrate = {
	JackDawADMachine : 1,
	JackDawADGplink : 1,
	JackDawADGPO : 1,
	JackDawADGroup : 1,
	JackDawADOU : 1,
	JackDawSD : 1,
	JackDawSPN : 1,
	JackDawADTrust : 1,
	JackDawADUser : 1,
	JackDawMachineConstrainedDelegation : 1,
	Credential : 1,
	JackDawCustomRelations : 1,
	HashEntry : 1,
	LocalGroup : 1,
	LSASecret : 1,
	LocalGroup : 1,
	NetSession : 1,
	NetShare : 1,
	SMBFinger : 1,
	JackDawSPNService : 1,
	JackDawTokenGroup : 1,	
}

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

def migrate_obj(session_old, session_new, ad_id, obj):
	session_old.query(obj).update({obj.ad_id : ad_id})
	session_old.commit()
	for res in session_old.query(obj).all():
		session_old.expunge(res)
		session_new.add(res)
	session_new.commit()

def migrate(args):
	session_old = get_session(args.old)
	session_new = get_session(args.new)

	for res in session_old.query(JackDawADInfo).all():
		ad_id = migrate_adifo(session_old, session_new, res)
		for obj in objs_to_migrate:
			print(type(obj))
			migrate_obj(session_old, session_new, ad_id, obj)



def main():
	import argparse
	parser = argparse.ArgumentParser(description='Gather gather gather')
	parser.add_argument('-v', '--verbose', action='count', default=0, help='Increase verbosity, can be stacked')
	parser.add_argument('old', help='SQL connection string.')
	parser.add_argument('new', help='SQL connection string.')
	args = parser.parse_args()

	migrate(args)


if __name__ == '__main__':
	main()
	
	
	