from . import Basemodel, lf
import hashlib
import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from jackdaw.dbmodel.utils.serializer import Serializer


class ADTrust(Basemodel, Serializer):
	__tablename__ = 'adtrusts'
	
	id = Column(Integer, primary_key=True)
	ad_id = Column(Integer, ForeignKey('adinfo.id'))
	cn = Column(String, index=True)
	dn = Column(String, index=True)
	guid = Column(String, index=True)
	
	name = Column(String, index=True)	
	whenChanged = Column(DateTime)	
	whenCreated = Column(DateTime)
	securityIdentifier = Column(String, index=True)
	trustDirection = Column(String, index = True)
	trustPartner = Column(String, index=True)
	trustPosixOffset = Column(Integer, index=True)
	trustType = Column(String, index = True)
	trustAttributes = Column(String, index=True)
	flatName = Column(String, index=True)

	checksum = Column(String, index = True)

	def gen_checksum(self):
		ctx = hashlib.md5()
		ctx.update(str(self.cn).encode())
		ctx.update(str(self.dn).encode())
		ctx.update(str(self.name).encode())
		ctx.update(str(self.whenCreated).encode())
		ctx.update(str(self.trustDirection).encode())
		ctx.update(str(self.trustPartner).encode())
		ctx.update(str(self.trustPosixOffset).encode())
		ctx.update(str(self.trustType).encode())
		ctx.update(str(self.trustAttributes).encode())
		ctx.update(str(self.flatName).encode())
		self.checksum = ctx.hexdigest()

	@staticmethod
	def from_ldapdict(d):
		trust = ADTrust()
		trust.cn = lf(d.get('cn'))
		trust.dn = lf(d.get('distinguishedName'))
		trust.guid = lf(d.get('objectGUID'))

		trust.name = lf(d.get('name'))
		trust.securityIdentifier = str(lf(d.get('securityIdentifier')))
		trust.whenChanged = lf(d.get('whenChanged'))
		trust.whenCreated = lf(d.get('whenCreated'))

		t = d.get('trustDirection')
		trust.trustDirection = t.name if t is not None else None
		trust.trustPartner = lf(d.get('trustPartner'))
		trust.trustPosixOffset = lf(d.get('trustPosixOffset'))
		t = d.get('trustType')
		trust.trustType = t.name if t is not None else None
		trust.trustAttributes = lf(d.get('trustAttributes'))
		trust.flatName = lf(d.get('flatName'))
		trust.gen_checksum()

		return trust


	def to_dict(self):
		return {
			'id' : self.id ,
			'ad_id' : self.ad_id ,
			'cn' : self.cn ,
			'dn' : self.dn ,
			'guid' : self.guid ,
			'name' : self.name ,
			'securityIdentifier' : self.securityIdentifier ,
			'whenChanged' : self.whenChanged ,
			'whenCreated' : self.whenCreated ,
			'trustDirection' : self.trustDirection ,
			'trustPartner' : self.trustPartner ,
			'trustPosixOffset' : self.trustPosixOffset ,
			'trustType' : self.trustType ,
			'trustAttributes' : self.trustAttributes ,
			'flatName' : self.flatName ,
			'checksum' : self.checksumm
		}