from . import Basemodel
import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean

from winacl.dtyp.ace import ADS_ACCESS_MASK, AceFlags
from jackdaw.dbmodel.utils.serializer import Serializer


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
		
hdr_flag_lookup = {
	AceFlags.CONTAINER_INHERIT_ACE : 'ace_hdr_flag_container_inherit',
	AceFlags.FAILED_ACCESS_ACE_FLAG : 'ace_hdr_flag_failed_access',
	AceFlags.INHERIT_ONLY_ACE : 'ace_hdr_flag_inherit_only',
	AceFlags.INHERITED_ACE : 'ace_hdr_flag_inherited',
	AceFlags.NO_PROPAGATE_INHERIT_ACE : 'ace_hdr_flag_no_propagate_inherit',
	AceFlags.OBJECT_INHERIT_ACE : 'ace_hdr_flag_object_inherit',
	AceFlags.SUCCESSFUL_ACCESS_ACE_FLAG : 'ace_hdr_flag_successful_access',
}

class NetDACL(Basemodel, Serializer):
	__tablename__ = 'netdacl'
	
	id = Column(Integer, primary_key=True)	
	
	object_id = Column(String, index=True)
	object_type = Column(String, index=True)
	
	owner_sid = Column(String, index=True)
	group_sid = Column(String, index=True)

	
	sd_control = Column(String, index=True)
	ace_type = Column(String, index=True)
	ace_mask = Column(String, index=True)
	ace_objecttype = Column(String, index=True)
	ace_inheritedobjecttype = Column(String, index=True)
	ace_sid = Column(String, index=True)
	ace_order = Column(Integer, index = True)
	
	#ace header flags
	
	ace_hdr_flag_container_inherit    = Column(Boolean, index = True)
	ace_hdr_flag_failed_access        = Column(Boolean, index = True)
	ace_hdr_flag_inherit_only         = Column(Boolean, index = True)
	ace_hdr_flag_inherited            = Column(Boolean, index = True)
	ace_hdr_flag_no_propagate_inherit = Column(Boolean, index = True)
	ace_hdr_flag_object_inherit       = Column(Boolean, index = True)
	ace_hdr_flag_successful_access    = Column(Boolean, index = True)
	
	#storing the bitfield in separate columns for easy lookup
	ace_mask_create_child   = Column(Boolean, index = True)
	ace_mask_delete_child   = Column(Boolean, index = True)
	ace_mask_actrl_ds_list  = Column(Boolean, index = True)
	ace_mask_self           = Column(Boolean, index = True)
	ace_mask_read_prop      = Column(Boolean, index = True)
	ace_mask_write_prop     = Column(Boolean, index = True)
	ace_mask_delete_tree    = Column(Boolean, index = True)
	ace_mask_list_object    = Column(Boolean, index = True)
	ace_mask_control_access = Column(Boolean, index = True)
	ace_mask_generic_read   = Column(Boolean, index = True)
	ace_mask_generic_write  = Column(Boolean, index = True)
	ace_mask_generic_execute = Column(Boolean, index = True)
	ace_mask_generic_all    = Column(Boolean, index = True)
	ace_mask_maximum_allowed = Column(Boolean, index = True)
	ace_mask_access_system_security = Column(Boolean, index = True)
	ace_mask_synchronize     = Column(Boolean, index = True)
	ace_mask_write_owner     = Column(Boolean, index = True)
	ace_mask_write_dacl      = Column(Boolean, index = True)
	ace_mask_read_control    = Column(Boolean, index = True)
	ace_mask_delete          = Column(Boolean, index = True)

	
	
	@staticmethod
	def hdrflag2attr(hdrflag):
		true_attrs = []
		false_attrs = []
		for hdr in hdr_flag_lookup:
			if hdrflag & hdr:
				true_attrs.append(hdr_flag_lookup[hdr])
			else:
				false_attrs.append(hdr_flag_lookup[hdr])

		return true_attrs, false_attrs
		
	
	@staticmethod
	def mask2attr(ace_mask):
		true_attrs = []
		false_attrs = []
		for am in am_lookup_table:
			if ace_mask & am:
				true_attrs.append(am_lookup_table[am])
			else:
				false_attrs.append(am_lookup_table[am])

		return true_attrs, false_attrs