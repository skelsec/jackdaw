from . import Basemodel
import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean

from winacl.dtyp.ace import ADS_ACCESS_MASK, AceFlags


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

class JackDawADDACL(Basemodel):
	__tablename__ = 'addacl'
	
	id = Column(Integer, primary_key=True)
	ad_id = Column(Integer, ForeignKey('ads.id'))
	#ad = relationship("JackDawADInfo", back_populates="objectacls", lazy = True)
	
	fetched_at = Column(DateTime, default=datetime.datetime.utcnow)
	guid = Column(String, index=True)
	sid = Column(String, index=True)
	
	object_type = Column(String, index=True)
	object_type_guid = Column(String, index=True)
	owner_sid = Column(String, index=True)
	group_sid = Column(String, index=True)
	
	cn = Column(String, index=True)
	dn = Column(String, index=True)
	
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