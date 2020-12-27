from . import Basemodel, lf, dt, bc
import datetime
import hashlib
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from jackdaw.dbmodel.utils.serializer import Serializer

class GPO(Basemodel, Serializer):
	__tablename__ = 'adgpo'

	id = Column(Integer, primary_key=True)
	ad_id = Column(Integer, ForeignKey('adinfo.id'))
	
	name = Column(String, index=True)
	dn = Column(String, index=True)
	cn = Column(String, index=True)
	flags = Column(Integer, index=True)
	path = Column(String, index=True)
	gPCFunctionalityVersion = Column(String, index=True)	
	objectClass = Column(String, index=True)
	objectGUID = Column(String, index=True)
	systemFlags = Column(Integer, index=True)
	whenChanged = Column(String, index=True)
	whenCreated = Column(String, index=True)
	gPCMachineExtensionNames = Column(String, index=True)
	gPCUserExtensionNames = Column(String, index=True)
	versionNumber = Column(String, index=True)

	checksum = Column(String, index = True)

	def gen_checksum(self):
		ctx = hashlib.md5()
		ctx.update(str(self.name).encode())
		ctx.update(str(self.dn).encode())
		ctx.update(str(self.cn).encode())
		ctx.update(str(self.flags).encode())
		ctx.update(str(self.path).encode())
		ctx.update(str(self.gPCFunctionalityVersion).encode())
		ctx.update(str(self.systemFlags).encode())
		ctx.update(str(self.gPCMachineExtensionNames).encode())
		ctx.update(str(self.gPCUserExtensionNames).encode())
		ctx.update(str(self.versionNumber).encode())
		self.checksum = ctx.hexdigest()
	
	def to_dict(self):
		return {
			'id' : self.id ,
			'ad_id' : self.ad_id ,
			'cn' : self.cn,
			'name' : self.name ,
			'dn' : self.dn ,
			'path' : self.path,
			'guid' : self.objectGUID,
			'whenChanged' : self.whenChanged ,
			'whenCreated' : self.whenCreated ,
			'gPCMachineExtensionNames' : self.gPCMachineExtensionNames ,
			'gPCUserExtensionNames' : self.gPCUserExtensionNames ,
			'versionNumber' : self.versionNumber ,
			'checksum' : self.checksum,
		}
	
	@staticmethod
	def from_adgpo(u):
		adou = GPO()
		adou.name = lf(u.displayName)
		adou.dn = lf(u.distinguishedName)
		adou.cn = lf(u.cn)
		adou.path = lf(u.gPCFileSysPath)
		adou.flags = lf(u.flags)
		adou.objectClass = lf(u.objectClass)
		adou.objectGUID = lf(u.objectGUID)
		adou.systemFlags = lf(u.systemFlags)
		adou.whenChanged = dt(lf(u.whenChanged))
		adou.whenCreated = dt(lf(u.whenCreated))
		adou.gPCMachineExtensionNames = lf(u.gPCMachineExtensionNames)
		adou.gPCUserExtensionNames = lf(u.gPCUserExtensionNames)
		adou.versionNumber = lf(u.versionNumber)

		adou.gen_checksum()
		
		return adou
		