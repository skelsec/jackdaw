#!/usr/bin/env python3
#
# Author:
#  Tamas Jos (@skelsec)
#

import multiprocessing as mp
import threading
import enum
import gzip
import json

from sqlalchemy import func
from sqlalchemy import not_, and_, or_, case
from sqlalchemy.orm import load_only

from jackdaw.dbmodel import get_session, windowed_query
from jackdaw.dbmodel.adsd import JackDawSD
from jackdaw.dbmodel.adinfo import ADInfo
from jackdaw.dbmodel.addacl import JackDawADDACL

from jackdaw import logger
from winacl.dtyp.security_descriptor import SECURITY_DESCRIPTOR
from jackdaw.wintypes.lookup_tables import *
import base64
from tqdm import tqdm


def ace_applies(ace_guid, object_class):
	'''
	Checks if an ACE applies to this object (based on object classes).
	Note that this function assumes you already verified that InheritedObjectType is set (via the flag).
	If this is not set, the ACE applies to all object types.
	'''
	try:
		our_ace_guid = OBJECTTYPE_GUID_MAP[object_class]
	except KeyError:
		return False
	if ace_guid == our_ace_guid:
		return True
	# If none of these match, the ACE does not apply to this object
	return False

def edge_calc_writer(outqueue, file_path, ad_id, append_to_file):
	"""
	Separate process to write all edges in a file as CSV
	"""
	try:
		buffer = ''
		if append_to_file is True:
			mode = 'a+'
		else:
			mode = 'w'
		
		with open(file_path, 'w', newline = '') as f:
			while True:
				data = outqueue.get()
				if data is None:
					return
				
				src, dst, label = data
				buffer += '%s,%s,%s,%s\r\n'
				if len(buffer) > 1000000:
					print('writing!')
					f.write(buffer)
					buffer = ''

	except Exception as e:
		logger.exception('edge_calc_writer')


def edge_calc_worker(inqueue, outqueue):
	while True:
		adsd = inqueue.get()

		if adsd is None:
			outqueue.put(None)
			return
		
		sd = SECURITY_DESCRIPTOR.from_bytes(base64.b64decode(adsd.sd))
		
		order_ctr = 0
		for ace in sd.Dacl.aces:
			acl = JackDawADDACL()
			acl.ad_id = adsd.ad_id
			acl.object_type = adsd.object_type
			acl.object_type_guid = OBJECTTYPE_GUID_MAP.get(adsd.object_type)
			acl.owner_sid = str(sd.Owner)
			acl.group_sid = str(sd.Group)
			acl.ace_order = order_ctr
			
			order_ctr += 1
			acl.guid = str(adsd.guid)
			if adsd.sid:
				acl.sid = str(adsd.sid)
			#if sd.cn:
			#	acl.cn = sd.cn
			#if sd.distinguishedName:
			#	acl.dn = str(sd.distinguishedName)
			acl.sd_control = sd.Control
			
			acl.ace_type = ace.AceType.name
			acl.ace_mask = ace.Mask
			t = getattr(ace,'ObjectType', None)
			if t:
				acl.ace_objecttype = str(t)
			
			t = getattr(ace,'InheritedObjectType', None)
			if t:
				acl.ace_inheritedobjecttype = str(t)
				
			true_attr, false_attr = JackDawADDACL.mask2attr(ace.Mask)
			
			for attr in true_attr:	
				setattr(acl, attr, True)
			for attr in false_attr:	
				setattr(acl, attr, False)
				
			true_attr, false_attr = JackDawADDACL.hdrflag2attr(ace.AceFlags)
			
			for attr in true_attr:	
				setattr(acl, attr, True)
			for attr in false_attr:	
				setattr(acl, attr, False)
			
			acl.ace_sid = str(ace.Sid)
			
			
			outqueue.put((acl.owner_sid, acl.sid, 'Owner'))

			if acl.ace_type not in ['ACCESS_ALLOWED_ACE_TYPE','ACCESS_ALLOWED_OBJECT_ACE_TYPE']:
				continue

			if acl.ace_type == 'ACCESS_ALLOWED_ACE_TYPE':
				if acl.ace_mask_generic_all == True:
					outqueue.put((acl.ace_sid, acl.sid, 'GenericALL'))

				if acl.ace_mask_generic_write == True:
					outqueue.put((acl.ace_sid, acl.sid, 'GenericWrite'))

				if acl.ace_mask_write_owner == True:
					outqueue.put((acl.ace_sid, acl.sid, 'WriteOwner'))

				if acl.ace_mask_write_dacl == True:
					outqueue.put((acl.ace_sid, acl.sid, 'WriteDacl'))

				if acl.object_type in ['user', 'domain'] and acl.ace_mask_control_access == True:
					outqueue.put((acl.ace_sid, acl.sid, 'ExtendedRightALL'))

			if acl.ace_type == 'ACCESS_ALLOWED_OBJECT_ACE_TYPE':
				if acl.ace_hdr_flag_inherited == True and acl.ace_hdr_flag_inherit_only == True:
					continue
				
				if acl.ace_hdr_flag_inherited == True and acl.ace_inheritedobjecttype is not None:
					if not ace_applies(acl.ace_inheritedobjecttype, acl.object_type):
						continue
					
				if any([acl.ace_mask_generic_all, acl.ace_mask_write_dacl, acl.ace_mask_write_owner, acl.ace_mask_generic_write]):
					if acl.ace_objecttype is not None and not ace_applies(acl.ace_objecttype, acl.object_type):
						continue
					
					if acl.ace_mask_generic_all == True:
						outqueue.put((acl.ace_sid, acl.sid, 'GenericALL'))
						continue
					
					if acl.ace_mask_generic_write == True:
						outqueue.put((acl.ace_sid, acl.sid, 'GenericWrite'))
						if acl.object_type != 'domain':
							continue
						
					if acl.ace_mask_write_dacl == True:
						outqueue.put((acl.ace_sid, acl.sid, 'WriteDacl'))

					if acl.ace_mask_write_owner == True:
						outqueue.put((acl.ace_sid, acl.sid, 'WriteOwner'))

				if acl.ace_mask_write_prop == True:
					if acl.object_type in ['user','group'] and acl.ace_objecttype is None:
						outqueue.put((acl.ace_sid, acl.sid, 'GenericWrite'))

					if acl.object_type == 'group' and acl.ace_objecttype == 'bf9679c0-0de6-11d0-a285-00aa003049e2':
						outqueue.put((acl.ace_sid, acl.sid, 'AddMember'))



				if acl.ace_mask_control_access == True:
					if acl.object_type in ['user','group'] and acl.ace_objecttype is None:
						outqueue.put((acl.ace_sid, acl.sid, 'ExtendedAll'))

					if acl.object_type == 'domain' and acl.ace_objecttype == '1131f6ad-9c07-11d1-f79f-00c04fc2dcd2':
						# 'Replicating Directory Changes All'
						outqueue.put((acl.ace_sid, acl.sid, 'GetChangesALL'))

					if acl.object_type == 'domain' and acl.ace_objecttype == '1131f6aa-9c07-11d1-f79f-00c04fc2dcd2':
						# 'Replicating Directory Changes'
						outqueue.put((acl.ace_sid, acl.sid, 'GetChanges'))

					if acl.object_type == 'user' and acl.ace_objecttype == '00299570-246d-11d0-a768-00aa006e0529':
						# 'Replicating Directory Changes'
						outqueue.put((acl.ace_sid, acl.sid, 'User-Force-Change-Password'))
		


class SDEgdeCalc:
	"""
	Polls all security descriptors from a db session given ad_id, then calculates all edges from all SDs and writes them to a file
	"""

	def __init__(self, session, ad_id, output_file_path, worker_count = None, buffer_size = 100000, append_to_file = True):
		self.session = session
		self.ad_id = ad_id
		self.append_to_file = append_to_file
		self.output_file_path = output_file_path
		self.buffer_size = buffer_size
		self.worker_count = worker_count
		if self.worker_count is None:
			self.worker_count = mp.cpu_count()
		
		self.workers = None
		self.writer = None
		self.inqueue = None
		self.outqueue = None

	def run(self):
		try:
			logger.debug('[ACL] Starting sd edge calc')
			self.inqueue = mp.Queue(self.buffer_size)
			self.outqueue = mp.Queue(self.buffer_size)
			logger.debug('[ACL] Starting processes')

			self.writer = mp.Process(target = edge_calc_writer, args = (self.outqueue, self.output_file_path, self.ad_id, self.append_to_file))
			self.writer.daemon = True
			self.writer.start()

			self.workers = [mp.Process(target = edge_calc_worker, args = (self.inqueue, self.outqueue)) for i in range(self.worker_count)]
			for proc in self.workers:
				proc.daemon = True
				proc.start()
				print(1)
			
			logger.debug('[ACL] data generation')

			total = self.session.query(func.count(JackDawSD.id)).filter_by(ad_id = self.ad_id).scalar()
			q = self.session.query(JackDawSD).filter_by(ad_id = self.ad_id)

			for adsd in tqdm(windowed_query(q, JackDawSD.id, 10), total=total):
				self.inqueue.put(adsd)

			for _ in range(procno):
				self.inqueue.put(None)
			logger.debug('Gen done!')

			logger.debug('[ACL] Added %s edges' % (p_cnt))

			logger.debug('[ACL] joining workers')
			for proc in self.workers:
				proc.join()

			logger.debug('[ACL] workers finished, waiting for writer')
			self.outqueue.put(None)
			self.writer.join()

			logger.debug('[ACL] All Finished!')

		except:
			logger.exception('[ACL]')
