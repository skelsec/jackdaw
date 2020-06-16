
import datetime

from winacl.dtyp.ace import ADS_ACCESS_MASK, AceFlags


#am_lookup_table = {
#			ADS_ACCESS_MASK.CREATE_CHILD : 'ace_mask_create_child',
#			ADS_ACCESS_MASK.DELETE_CHILD : 'ace_mask_delete_child',
#			ADS_ACCESS_MASK.ACTRL_DS_LIST : 'ace_mask_actrl_ds_list',
#			ADS_ACCESS_MASK.SELF : 'ace_mask_self',
#			ADS_ACCESS_MASK.READ_PROP : 'ace_mask_read_prop',
#			ADS_ACCESS_MASK.WRITE_PROP : 'ace_mask_write_prop',
#			ADS_ACCESS_MASK.DELETE_TREE : 'ace_mask_delete_tree',
#			ADS_ACCESS_MASK.LIST_OBJECT : 'ace_mask_list_object',
#			ADS_ACCESS_MASK.CONTROL_ACCESS : 'ace_mask_control_access',
#			ADS_ACCESS_MASK.DELETE : 'ace_mask_delete',
#			ADS_ACCESS_MASK.READ_CONTROL : 'ace_mask_read_control',
#			ADS_ACCESS_MASK.WRITE_DACL : 'ace_mask_write_dacl',
#			ADS_ACCESS_MASK.WRITE_OWNER : 'ace_mask_write_owner',
#			ADS_ACCESS_MASK.SYNCHRONIZE : 'ace_mask_synchronize',
#			ADS_ACCESS_MASK.ACCESS_SYSTEM_SECURITY : 'ace_mask_access_system_security',
#			ADS_ACCESS_MASK.MAXIMUM_ALLOWED : 'ace_mask_maximum_allowed',
#			ADS_ACCESS_MASK.GENERIC_ALL : 'ace_mask_generic_all',
#			ADS_ACCESS_MASK.GENERIC_EXECUTE : 'ace_mask_generic_execute',
#			ADS_ACCESS_MASK.GENERIC_WRITE : 'ace_mask_generic_write',
#			ADS_ACCESS_MASK.GENERIC_READ : 'ace_mask_generic_read',
#		}
#		
#hdr_flag_lookup = {
#	AceFlags.CONTAINER_INHERIT_ACE : 'ace_hdr_flag_container_inherit',
#	AceFlags.FAILED_ACCESS_ACE_FLAG : 'ace_hdr_flag_failed_access',
#	AceFlags.INHERIT_ONLY_ACE : 'ace_hdr_flag_inherit_only',
#	AceFlags.INHERITED_ACE : 'ace_hdr_flag_inherited',
#	AceFlags.NO_PROPAGATE_INHERIT_ACE : 'ace_hdr_flag_no_propagate_inherit',
#	AceFlags.OBJECT_INHERIT_ACE : 'ace_hdr_flag_object_inherit',
#	AceFlags.SUCCESSFUL_ACCESS_ACE_FLAG : 'ace_hdr_flag_successful_access',
#}

class JackDawADDACL:
	def __init__(self):
		self.ad_id = None
		self.guid = None
		self.sid = None
		
		self.object_type = None
		self.object_type_guid = None
		self.owner_sid = None
		self.group_sid = None
		
		self.cn = None
		self.dn = None
		
		self.sd_control = None
		self.ace_type = None
		self.ace_mask = None
		self.ace_objecttype = None
		self.ace_inheritedobjecttype = None
		self.ace_sid     = None
		self.ace_order   = None
		
		#ace header flags
		
		self.ace_hdr_flag_container_inherit    = None
		self.ace_hdr_flag_failed_access        = None
		self.ace_hdr_flag_inherit_only         = None
		self.ace_hdr_flag_inherited            = None
		self.ace_hdr_flag_no_propagate_inherit = None
		self.ace_hdr_flag_object_inherit       = None
		self.ace_hdr_flag_successful_access    = None
		
		#storing the bitfield in separate columns for easy lookup
		self.ace_mask_create_child    = None
		self.ace_mask_delete_child    = None
		self.ace_mask_actrl_ds_list   = None
		self.ace_mask_self            = None
		self.ace_mask_read_prop       = None
		self.ace_mask_write_prop      = None
		self.ace_mask_delete_tree     = None
		self.ace_mask_list_object     = None
		self.ace_mask_control_access  = None
		self.ace_mask_generic_read    = None
		self.ace_mask_generic_write   = None
		self.ace_mask_generic_execute = None
		self.ace_mask_generic_all     = None
		self.ace_mask_maximum_allowed = None
		self.ace_mask_access_system_security = None
		self.ace_mask_synchronize     = None
		self.ace_mask_write_owner     = None
		self.ace_mask_write_dacl      = None
		self.ace_mask_read_control    = None
		self.ace_mask_delete          = None
#
#	def add_ads_mask(self, ads_mask):
#		self.ace_mask_create_child   = True if ads_mask & ADS_ACCESS_MASK.CREATE_CHILD else False
#		self.ace_mask_delete_child   = True if ads_mask & ADS_ACCESS_MASK.DELETE_CHILD else False
#		self.ace_mask_actrl_ds_list  = True if ads_mask & ADS_ACCESS_MASK.ACTRL_DS_LIST else False
#		self.ace_mask_self           = True if ads_mask & ADS_ACCESS_MASK.SELF else False
#		self.ace_mask_read_prop      = True if ads_mask & ADS_ACCESS_MASK.READ_PROP else False
#		self.ace_mask_write_prop     = True if ads_mask & ADS_ACCESS_MASK.WRITE_PROP else False
#		self.ace_mask_delete_tree    = True if ads_mask & ADS_ACCESS_MASK.DELETE_TREE else False
#		self.ace_mask_list_object    = True if ads_mask & ADS_ACCESS_MASK.LIST_OBJECT else False
#		self.ace_mask_control_access = True if ads_mask & ADS_ACCESS_MASK.CONTROL_ACCESS else False
#		self.ace_mask_generic_read   = True if ads_mask & ADS_ACCESS_MASK.GENERIC_READ else False
#		self.ace_mask_generic_write  = True if ads_mask & ADS_ACCESS_MASK.GENERIC_WRITE else False
#		self.ace_mask_generic_execute = True if ads_mask & ADS_ACCESS_MASK.GENERIC_EXECUTE else False
#		self.ace_mask_generic_all    = True if ads_mask & ADS_ACCESS_MASK.GENERIC_ALL else False
#		self.ace_mask_maximum_allowed = True if ads_mask & ADS_ACCESS_MASK.MAXIMUM_ALLOWED else False
#		self.ace_mask_access_system_security = True if ads_mask & ADS_ACCESS_MASK.ACCESS_SYSTEM_SECURITY else False
#		self.ace_mask_synchronize     = True if ads_mask & ADS_ACCESS_MASK.SYNCHRONIZE else False
#		self.ace_mask_write_owner     = True if ads_mask & ADS_ACCESS_MASK.WRITE_OWNER else False
#		self.ace_mask_write_dacl      = True if ads_mask & ADS_ACCESS_MASK.WRITE_DACL else False
#		self.ace_mask_read_control    = True if ads_mask & ADS_ACCESS_MASK.READ_CONTROL else False
#		self.ace_mask_delete          = True if ads_mask & ADS_ACCESS_MASK.DELETE else False
#	
#	def add_hdr_mask(self, mask):
#		self.ace_hdr_flag_container_inherit    = True if mask & AceFlags.CONTAINER_INHERIT_ACE else False
#		self.ace_hdr_flag_failed_access        = True if mask & AceFlags.FAILED_ACCESS_ACE_FLAG else False
#		self.ace_hdr_flag_inherit_only         = True if mask & AceFlags.INHERIT_ONLY_ACE else False
#		self.ace_hdr_flag_inherited            = True if mask & AceFlags.INHERITED_ACE else False
#		self.ace_hdr_flag_no_propagate_inherit = True if mask & AceFlags.NO_PROPAGATE_INHERIT_ACE else False
#		self.ace_hdr_flag_object_inherit       = True if mask & AceFlags.OBJECT_INHERIT_ACE else False
#		self.ace_hdr_flag_successful_access    = True if mask & AceFlags.SUCCESSFUL_ACCESS_ACE_FLAG else False
	
#	@staticmethod
#	def hdrflag2attr(hdrflag):
#		true_attrs = []
#		false_attrs = []
#		for hdr in hdr_flag_lookup:
#			if hdrflag & hdr:
#				true_attrs.append(hdr_flag_lookup[hdr])
#			else:
#				false_attrs.append(hdr_flag_lookup[hdr])
#
#		return true_attrs, false_attrs
#		
#	
#	@staticmethod
#	def mask2attr(ace_mask):
#		true_attrs = []
#		false_attrs = []
#		for am in am_lookup_table:
#			if ace_mask & am:
#				true_attrs.append(am_lookup_table[am])
#			else:
#				false_attrs.append(am_lookup_table[am])
#
#		return true_attrs, false_attrs