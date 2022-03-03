#!/usr/bin/env python3
#
# Author:
#  Tamas Jos (@skelsec)
#

import threading
import enum
import gzip
import json

try:
	import multiprocessing as mp
except ImportError:
	mp = None

from sqlalchemy import func
from sqlalchemy import not_, and_, or_, case
from sqlalchemy.orm import load_only

from jackdaw.dbmodel import get_session, windowed_query
from jackdaw.dbmodel.adsd import JackDawSD
from jackdaw.dbmodel.adinfo import ADInfo
from jackdaw.dbmodel.utils.addacl import JackDawADDACL
from winacl.dtyp.ace import ADS_ACCESS_MASK, AceFlags
from jackdaw import logger
from winacl.dtyp.security_descriptor import SECURITY_DESCRIPTOR
from jackdaw.wintypes.lookup_tables import *
import base64
from tqdm import tqdm
from gzip import GzipFile
import io


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
		buffer = b''
		if append_to_file is True:
			mode = 'ab+'
		else:
			mode = 'wb'

		with GzipFile(file_path,mode) as f:
			while True:
				data = outqueue.get()
				if data is None:
					return
				f.write(data)

	except Exception as e:
		logger.exception('edge_calc_writer')

def calc_sd_edges(adsd):
	def helper(src,dst,label, ad_id = 1):
		return [src,dst,label,ad_id]
	
	if adsd.sd is None:
		#print('No security descriptor! %s' % adsd.id)
		return []

	buffer = []
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
		
		ace.Mask = ADS_ACCESS_MASK(ace.Mask)
		acl.ace_sid = str(ace.Sid)

		buffer.append(helper(acl.owner_sid, acl.sid, 'Owner'))

		if acl.ace_type not in ['ACCESS_ALLOWED_ACE_TYPE','ACCESS_ALLOWED_OBJECT_ACE_TYPE']:
			continue

		if acl.ace_type == 'ACCESS_ALLOWED_ACE_TYPE':
			if ADS_ACCESS_MASK.GENERIC_ALL in ace.Mask:
				buffer.append(helper(acl.ace_sid, acl.sid, 'GenericALL'))

			if ADS_ACCESS_MASK.GENERIC_WRITE in ace.Mask:
				buffer.append(helper(acl.ace_sid, acl.sid, 'GenericWrite'))

			if ADS_ACCESS_MASK.WRITE_OWNER in ace.Mask:
				buffer.append(helper(acl.ace_sid, acl.sid, 'WriteOwner'))

			if ADS_ACCESS_MASK.WRITE_DACL in ace.Mask:
				buffer.append(helper(acl.ace_sid, acl.sid, 'WriteDacl'))

			if acl.object_type in ['user', 'domain'] and ADS_ACCESS_MASK.CONTROL_ACCESS in ace.Mask: 
				buffer.append(helper(acl.ace_sid, acl.sid, 'ExtendedRightALL'))

		if acl.ace_type == 'ACCESS_ALLOWED_OBJECT_ACE_TYPE':
			if AceFlags.INHERITED_ACE in ace.AceFlags and AceFlags.INHERIT_ONLY_ACE in ace.AceFlags:
				continue
				
			if AceFlags.INHERITED_ACE in ace.AceFlags and acl.ace_inheritedobjecttype is not None:
				if not ace_applies(acl.ace_inheritedobjecttype, acl.object_type):
					continue
					
			if (ADS_ACCESS_MASK.GENERIC_ALL in ace.Mask) or (ADS_ACCESS_MASK.WRITE_DACL in ace.Mask) or (ADS_ACCESS_MASK.WRITE_OWNER in ace.Mask) or (ADS_ACCESS_MASK.GENERIC_WRITE in ace.Mask):
				if acl.ace_objecttype is not None and not ace_applies(acl.ace_objecttype, acl.object_type):
					continue
					
				if ADS_ACCESS_MASK.GENERIC_ALL in ace.Mask:
					buffer.append(helper(acl.ace_sid, acl.sid, 'GenericALL'))
					continue
					
				if ADS_ACCESS_MASK.GENERIC_WRITE in ace.Mask:
					buffer.append(helper(acl.ace_sid, acl.sid, 'GenericWrite'))
					if acl.object_type != 'domain':
						continue
						
				if ADS_ACCESS_MASK.WRITE_DACL in ace.Mask:
					buffer.append(helper(acl.ace_sid, acl.sid, 'WriteDacl'))

				if ADS_ACCESS_MASK.WRITE_OWNER in ace.Mask:
					buffer.append(helper(acl.ace_sid, acl.sid, 'WriteOwner'))

			if ADS_ACCESS_MASK.WRITE_PROP in ace.Mask:
				if acl.object_type in ['user','group'] and acl.ace_objecttype is None:
					buffer.append(helper(acl.ace_sid, acl.sid, 'GenericWrite'))

				if acl.object_type == 'group' and acl.ace_objecttype == 'bf9679c0-0de6-11d0-a285-00aa003049e2':
					buffer.append(helper(acl.ace_sid, acl.sid, 'AddMember'))


			if ADS_ACCESS_MASK.CONTROL_ACCESS in ace.Mask:
				if acl.object_type in ['user','group'] and acl.ace_objecttype is None:
					buffer.append(helper(acl.ace_sid, acl.sid, 'ExtendedAll'))

				if acl.object_type == 'domain' and acl.ace_objecttype == '1131f6ad-9c07-11d1-f79f-00c04fc2dcd2':
					# 'Replicating Directory Changes All'
					buffer.append(helper(acl.ace_sid, acl.sid, 'GetChangesALL'))

				if acl.object_type == 'domain' and acl.ace_objecttype == '1131f6aa-9c07-11d1-f79f-00c04fc2dcd2':
					# 'Replicating Directory Changes'
					buffer.append(helper(acl.ace_sid, acl.sid, 'GetChanges'))

				if acl.object_type == 'user' and acl.ace_objecttype == '00299570-246d-11d0-a768-00aa006e0529':
					# 'Replicating Directory Changes'
					buffer.append(helper(acl.ace_sid, acl.sid, 'User-Force-Change-Password'))
				
	return buffer

class SDEgdeCalc:
	"""
	Polls all security descriptors from a db session given ad_id, then calculates all edges from all SDs and writes them to a file
	"""

	def __init__(self, session, ad_id, worker_count = None, buffer_size = 100):
		self.session = session
		self.ad_id = ad_id
		self.buffer_size = buffer_size
		self.worker_count = worker_count
		if self.worker_count is None:
			self.worker_count = mp.cpu_count() if mp is not None else 1
		
		self.workers = None
		self.writer = None
		self.inqueue = None
		self.outqueue = None

	def run(self):
		try:
			logger.debug('[ACL] Starting sd edge calc')
			logger.debug('[ACL] data generation')

			total = self.session.query(func.count(JackDawSD.id)).filter_by(ad_id = self.ad_id).scalar()
			q = self.session.query(JackDawSD).filter_by(ad_id = self.ad_id)

			for adsd in tqdm(windowed_query(q, JackDawSD.id, self.worker_count), total=total):
				self.inqueue.put(adsd)


			logger.debug('[ACL] All Finished!')

		except:
			logger.exception('[ACL]')

if __name__ == '__main__':
	class Test():
		def __init__(self):
			self.id = 1
			self.ad_id = 1
			self.guid = 'd971c60d-952a-42c4-99b8-dad282afe1f3'
			self.sid = 'S-1-5-21-3448413973-1765323015-1500960949-1109'
			self.object_type = 'machine'
			self.sd_hash = 'a'
			self.sd = 'AQAEjHQKAACQCgAAAAAAABQAAAAEAGAKNAAAAAUASAAgAAAAAwAAABAgIF+ledARkCAAwE/C1M+Gepa/5g3QEaKFAKoAMEniAQUAAAAAAAUVAAAAFZ+KzQexOGm12HZZAAIAAAUASAAgAAAAAwAAAFB5lr/mDdARooUAqgAwSeKGepa/5g3QEaKFAKoAMEniAQUAAAAAAAUVAAAAFZ+KzQexOGm12HZZAAIAAAUASAAgAAAAAwAAAFN5lr/mDdARooUAqgAwSeKGepa/5g3QEaKFAKoAMEniAQUAAAAAAAUVAAAAFZ+KzQexOGm12HZZAAIAAAUASAAgAAAAAwAAANC/Cj5qEtARoGAAqgBsM+2Gepa/5g3QEaKFAKoAMEniAQUAAAAAAAUVAAAAFZ+KzQexOGm12HZZAAIAAAUKSAAQAAAAAwAAAL80zBwySlRNu4k65aCed3GGepa/5g3QEaKFAKoAMEniAQUAAAAAAAUVAAAAFZ+KzQexOGm12HZZAAIAAAUKSAAQAQAAAwAAAB40gbPnaQ9HmEPdnE/zhKGGepa/5g3QEaKFAKoAMEniAQUAAAAAAAUVAAAAFZ+KzQexOGm12HZZAAIAAAUAOAAIAAAAAQAAAEeV43IYe9ERre8AwE/Y1c0BBQAAAAAABRUAAAAVn4rNB7E4abXYdlkAAgAABQA4AAgAAAABAAAAiEem8wZT0RGpxQAA+ANnwQEFAAAAAAAFFQAAABWfis0HsThptdh2WQACAAAFADgAIAAAAAEAAAAAQhZMwCDQEadoAKoAbgUpAQUAAAAAAAUVAAAAFZ+KzQexOGm12HZZAAIAAAUAOAAwAAAAAQAAAH96lr/mDdARooUAqgAwSeIBBQAAAAAABRUAAAAVn4rNB7E4abXYdlkFAgAABQo4ACAAAAADAAAAHjSBs+dpD0eYQ92cT/OEoYZ6lr/mDdARooUAqgAwSeIBAQAAAAAABQoAAAAFCjgAMAAAAAMAAAC/NMwcMkpUTbuJOuWgnndxhnqWv+YN0BGihQCqADBJ4gEBAAAAAAAFCgAAAAUALAADAAAAAQAAAKh6lr/mDdARooUAqgAwSeIBAgAAAAAABSAAAAAmAgAABQAsABAAAAABAAAAHbGpRq5gWkC36P+KWNRW0gECAAAAAAAFIAAAADACAAAFACgAAAEAAAEAAABTGnKrLx7QEZgZAKoAQFKbAQEAAAAAAAEAAAAABQAoAAgAAAABAAAAR5Xjchh70RGt7wDAT9jVzQEBAAAAAAAFCgAAAAUAKAAIAAAAAQAAAIhHpvMGU9ERqcUAAPgDZ8EBAQAAAAAABQoAAAAFACgAMAAAAAEAAACGuLV3SpTREa69AAD4A2fBAQEAAAAAAAUKAAAAAAAkAP8BDwABBQAAAAAABRUAAAAVn4rNB7E4abXYdlkAAgAAAAAYAP8BDwABAgAAAAAABSAAAAAkAgAAAAAUAAMAAAABAQAAAAAABQoAAAAAABQAlAACAAEBAAAAAAAFCwAAAAAAFAD/AQ8AAQEAAAAAAAUSAAAABRI4ACAAAAADAAAAHjSBs+dpD0eYQ92cT/OEoYZ6lr/mDdARooUAqgAwSeIBAQAAAAAABQoAAAAFEjgAMAAAAAMAAAC/NMwcMkpUTbuJOuWgnndxhnqWv+YN0BGihQCqADBJ4gEBAAAAAAAFCgAAAAUaPAAQAAAAAwAAAABCFkzAINARp2gAqgBuBSkUzChINxS8RZsHrW8BXl8oAQIAAAAAAAUgAAAAKgIAAAUaPAAQAAAAAwAAAABCFkzAINARp2gAqgBuBSm6epa/5g3QEaKFAKoAMEniAQIAAAAAAAUgAAAAKgIAAAUaPAAQAAAAAwAAABAgIF+ledARkCAAwE/C1M8UzChINxS8RZsHrW8BXl8oAQIAAAAAAAUgAAAAKgIAAAUaPAAQAAAAAwAAABAgIF+ledARkCAAwE/C1M+6epa/5g3QEaKFAKoAMEniAQIAAAAAAAUgAAAAKgIAAAUaPAAQAAAAAwAAAEDCCrypedARkCAAwE/C1M8UzChINxS8RZsHrW8BXl8oAQIAAAAAAAUgAAAAKgIAAAUaPAAQAAAAAwAAAEDCCrypedARkCAAwE/C1M+6epa/5g3QEaKFAKoAMEniAQIAAAAAAAUgAAAAKgIAAAUaPAAQAAAAAwAAAEIvulmiedARkCAAwE/C088UzChINxS8RZsHrW8BXl8oAQIAAAAAAAUgAAAAKgIAAAUaPAAQAAAAAwAAAEIvulmiedARkCAAwE/C08+6epa/5g3QEaKFAKoAMEniAQIAAAAAAAUgAAAAKgIAAAUaPAAQAAAAAwAAAPiIcAPhCtIRtCIAoMlo+TkUzChINxS8RZsHrW8BXl8oAQIAAAAAAAUgAAAAKgIAAAUaPAAQAAAAAwAAAPiIcAPhCtIRtCIAoMlo+Tm6epa/5g3QEaKFAKoAMEniAQIAAAAAAAUgAAAAKgIAAAUSOAAwAAAAAQAAAA/WR1uQYLJAnzcqTeiPMGMBBQAAAAAABRUAAAAVn4rNB7E4abXYdlkOAgAABRI4ADAAAAABAAAAD9ZHW5BgskCfNypN6I8wYwEFAAAAAAAFFQAAABWfis0HsThptdh2WQ8CAAAFEDgACAAAAAEAAACmbQKbPA1cRovuUZnXFly6AQUAAAAAAAUVAAAAFZ+KzQexOGm12HZZAAIAAAUaOAAIAAAAAwAAAKZtAps8DVxGi+5RmdcWXLqGepa/5g3QEaKFAKoAMEniAQEAAAAAAAMAAAAABRI4AAgAAAADAAAApm0CmzwNXEaL7lGZ1xZcuoZ6lr/mDdARooUAqgAwSeIBAQAAAAAABQoAAAAFEjgAEAAAAAMAAABtnsa3xyzSEYVOAKDJg/YIhnqWv+YN0BGihQCqADBJ4gEBAAAAAAAFCQAAAAUaOAAQAAAAAwAAAG2exrfHLNIRhU4AoMmD9gicepa/5g3QEaKFAKoAMEniAQEAAAAAAAUJAAAABRo4ABAAAAADAAAAbZ7Gt8cs0hGFTgCgyYP2CLp6lr/mDdARooUAqgAwSeIBAQAAAAAABQkAAAAFEjgAIAAAAAMAAACTexvqSF7VRrxsTfT9p4o1hnqWv+YN0BGihQCqADBJ4gEBAAAAAAAFCgAAAAUaLACUAAIAAgAAABTMKEg3FLxFmwetbwFeXygBAgAAAAAABSAAAAAqAgAABRosAJQAAgACAAAAnHqWv+YN0BGihQCqADBJ4gECAAAAAAAFIAAAACoCAAAFGiwAlAACAAIAAAC6epa/5g3QEaKFAKoAMEniAQIAAAAAAAUgAAAAKgIAAAUTKAAwAAAAAQAAAOXDeD+a971GoLidGBFt3HkBAQAAAAAABQoAAAAFEigAMAEAAAEAAADeR+aRb9lwS5VX1j/088zYAQEAAAAAAAUKAAAAABIkAP8BDwABBQAAAAAABRUAAAAVn4rNB7E4abXYdlkHAgAAABIYAAQAAAABAgAAAAAABSAAAAAqAgAAABIYAL0BDwABAgAAAAAABSAAAAAgAgAAAQUAAAAAAAUVAAAAFZ+KzQexOGm12HZZAAIAAAEFAAAAAAAFFQAAABWfis0HsThptdh2WQACAAA='

	adsd = Test()
	for _ in range(10000):
		calc_sd_edges(adsd)