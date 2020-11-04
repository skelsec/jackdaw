


from . import Basemodel
import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
import json
from jackdaw.dbmodel.utils.serializer import Serializer

class ADSchemaEntry(Basemodel, Serializer):
	__tablename__ = 'adschemaentry'
	
	id = Column(Integer, primary_key=True)
	ad_id = Column(Integer, ForeignKey('adinfo.id'))
	
	cn = Column(String)
	dn = Column(String)
	adminDescription = Column(String)
	adminDisplayName = Column(String)
	objectGUID = Column(String, index=True)
	schemaIDGUID = Column(String, index=True)
	lDAPDisplayName = Column(String, index=True)
	name = Column(String, index=True)


	@staticmethod
	def from_adschemaentry(u):
		schema = ADSchemaEntry()
		schema.cn = u.cn
		schema.dn = u.distinguishedName
		schema.adminDescription = u.adminDescription
		schema.adminDisplayName = u.adminDisplayName
		schema.objectGUID = u.objectGUID
		schema.schemaIDGUID = u.schemaIDGUID
		schema.lDAPDisplayName = u.lDAPDisplayName
		schema.name = u.name

		return schema
