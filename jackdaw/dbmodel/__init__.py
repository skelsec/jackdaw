import datetime
import logging

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey, Table, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
import enum

Basemodel = declarative_base()

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
	if x == '':
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

from .adacl import *
from .adgroup import *
from .adcomp import *
from .adinfo import *
from .aduser import *
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
