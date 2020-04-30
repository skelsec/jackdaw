import datetime
import logging

from sqlalchemy.engine import Engine
from sqlalchemy import event
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey, Table, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
import enum

from winacl.dtyp.ace import ADS_ACCESS_MASK, AceFlags

Basemodel = declarative_base()



@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
	##
	## This function runs after the sqlite connection is made, and speeds up the insert operations considerably
	## Sadly I could not find a way to limit the execution to sqlite so other DBs will trow an error :(
	## TODO: fix this
	##
	cursor = dbapi_connection.cursor()
	cursor.execute("PRAGMA journal_mode = MEMORY")
	cursor.execute("PRAGMA synchronous = OFF")
	cursor.execute("PRAGMA temp_store = MEMORY")
	cursor.execute("PRAGMA cache_size = 500000")
	cursor.close()

def lf(x, sep = ','):
	"""
	flattens objects
	"""
	if isinstance(x, list):
		return sep.join(x)
	elif isinstance(x, (datetime.datetime, int, enum.IntFlag)):
		return x
	return str(x)
	
def dt(x):
	"""
	datetime corrections
	"""
	if x in ['', None, 'None']:
		return None
	if isinstance(x, str):
		return datetime.datetime.fromisoformat(x)
	if not isinstance(x,datetime.datetime):
		print(x)
	return x
	
def bc(x):
	"""
	boolean corrections
	"""
	if x is None:
		return None
	if isinstance(x,bool):
		return x
	if isinstance(x, str):
		if x.upper() == 'TRUE':
			return True
		elif x.upper() == 'FALSE':
			return False
		elif x.upper() == 'NONE':
			return None
	raise Exception('Cant convert this to bool: %s type: %s' % (x, type(x)))

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
from .usergroup import *
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



def create_db(connection, verbosity = 0):
	logging.info('Creating database %s' % connection)
	engine = create_engine(connection, echo=True if verbosity > 1 else False) #'sqlite:///dump.db'	
	Basemodel.metadata.create_all(engine)
	logging.info('Done creating database %s' % connection)

def get_session(connection, verbosity = 0):
	logging.debug('Connecting to DB')
	engine = create_engine(connection, echo=True if verbosity > 1 else False) #'sqlite:///dump.db'	
	logging.debug('Creating session')
	# create a configured "Session" class
	Session = sessionmaker(bind=engine)
	# create a Session
	return Session()
	
	
am_lookup_table = {
			ADS_ACCESS_MASK.CREATE_CHILD : 'ace_mask_create_child',
			ADS_ACCESS_MASK.DELETE_CHILD : 'ace_mask_delete_child',
			ADS_ACCESS_MASK.ACTRL_DS_LIST : 'ace_mask_actrl_ds_list',
			ADS_ACCESS_MASK.SELF : 'ace_mask_self',
			ADS_ACCESS_MASK.READ_PROP : 'ace_mask_read_prop',
			ADS_ACCESS_MASK.WRITE_PROP : 'ace_mask_write_prop',
			ADS_ACCESS_MASK.DELETE_TREE : 'ace_mask_delete_tree',
			ADS_ACCESS_MASK.LIST_OBJECT : 'ace_mask_list_object',
			ADS_ACCESS_MASK.CONTROL_ACCESS : 'ace_mask_control_access',
			ADS_ACCESS_MASK.DELETE : 'ace_mask_delete',
			ADS_ACCESS_MASK.READ_CONTROL : 'ace_mask_read_control',
			ADS_ACCESS_MASK.WRITE_DACL : 'ace_mask_write_dacl',
			ADS_ACCESS_MASK.WRITE_OWNER : 'ace_mask_write_owner',
			ADS_ACCESS_MASK.SYNCHRONIZE : 'ace_mask_synchronize',
			ADS_ACCESS_MASK.ACCESS_SYSTEM_SECURITY : 'ace_mask_access_system_security',
			ADS_ACCESS_MASK.MAXIMUM_ALLOWED : 'ace_mask_maximum_allowed',
			ADS_ACCESS_MASK.GENERIC_ALL : 'ace_mask_generic_all',
			ADS_ACCESS_MASK.GENERIC_EXECUTE : 'ace_mask_generic_execute',
			ADS_ACCESS_MASK.GENERIC_WRITE : 'ace_mask_generic_write',
			ADS_ACCESS_MASK.GENERIC_READ : 'ace_mask_generic_read',
		}
