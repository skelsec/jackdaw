import traceback
import os
import base64
from jackdaw.dbmodel.spnservice import SPNService
from jackdaw.dbmodel.addacl import JackDawADDACL
from jackdaw.dbmodel.adsd import JackDawSD
from winacl.dtyp.security_descriptor import SECURITY_DESCRIPTOR

from jackdaw.dbmodel import *
from jackdaw.wintypes.lookup_tables import *
from jackdaw import logger




def store_sd(session, ad_id, obj_type,objectGUID, objectSid, sd):
		#print('Got SD object!')
		obj_type = obj_type
		order_ctr = 0
		for ace in sd.Dacl.aces:
			acl = JackDawADDACL()
			acl.ad_id = ad_id
			acl.object_type = obj_type
			acl.object_type_guid = OBJECTTYPE_GUID_MAP.get(obj_type)
			acl.owner_sid = str(sd.Owner)
			acl.group_sid = str(sd.Group)
			acl.ace_order = order_ctr
			
			order_ctr += 1
			acl.guid = str(objectGUID)
			acl.sd_control = sd.Control
			acl.sid = objectSid
			
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
			session.add(acl)
		
		session.commit()

def main():
	import sys
	sql = sys.argv[1]
	ad_id = sys.argv[2]
	session = get_session(sql)

	for res in session.query(JackDawSD).filter_by(ad_id=ad_id).all():
		sd = SECURITY_DESCRIPTOR.from_bytes(base64.b64decode(res.sd))
		#print(sd)
		store_sd(session, ad_id, res.object_type, res.guid, res.sid, sd)



if __name__ == '__main__':
	main()