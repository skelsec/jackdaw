from . import Basemodel
from sqlalchemy import Column, Integer, String, DateTime
from jackdaw.dbmodel.utils.serializer import Serializer
from jackdaw.utils.encoder import UniversalEncoder 
import json

JD_SMBFILE_TSV_HDR = ['otype', 'unc', 'size', 'size_ext', 'creation_time', 'last_access_time', 'last_write_time', 'change_time', 'ad_id','machine_sid', 'sddl']

class SMBFile(Basemodel, Serializer):
	__tablename__ = 'smbfile'
	
	id = Column(Integer, primary_key=True)
	ad_id = Column(Integer, index=True)
	machine_sid = Column(String, index=True)
	otype = Column(String, index=True)
	unc = Column(String, index=True)
	size = Column(Integer, index=True)
	size_ext = Column(Integer, index=True)
	creation_time = Column(DateTime)
	last_access_time = Column(DateTime)
	last_write_time = Column(DateTime)
	change_time = Column(DateTime)
	sddl = Column(Integer, index=True)

	def to_dict(self):
		return {
			'ad_id' : self.ad_id ,
			'machine_sid' : self.machine_sid ,
			'otype' : self.otype,
			'unc' : self.unc ,
			'size' : self.size ,
			'size_ext' : self.size_ext ,
			'creation_time' : self.creation_time , 
			'last_access_time' : self.last_access_time , 
			'last_write_time' : self.last_write_time , 
			'change_time' : self.change_time , 
			'sddl' : self.sddl,
		}
	
	def to_json(self):
		return json.dumps(self.to_dict(), cls = UniversalEncoder)
	
	def to_tsv(self, separator = '\t'):
		dd = self.to_dict()
		t = [str(dd[key]) for key in JD_SMBFILE_TSV_HDR]
		return separator.join(t)