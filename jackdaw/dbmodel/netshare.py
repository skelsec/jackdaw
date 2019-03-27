from . import Basemodel
import datetime
from sqlalchemy import Column, Integer, String, DateTime

class NetShare(Basemodel):
	__tablename__ = 'netshare'
	
	id = Column(Integer, primary_key=True)
	fetched_at = Column(DateTime, default=datetime.datetime.utcnow)
	ip = Column(String, index=True)
	rdns = Column(String, index=True)
	netname = Column(String, index=True)
	type = Column(String, index=True)
	remark = Column(String, index=True)
	passwd = Column(String, index=True)
	