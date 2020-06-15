from flask import current_app
from jackdaw.dbmodel.netshare import NetShare
import string

def get_by_id(shareid):
	db = current_app.db
	res = db.session.query(NetShare).get(shareid)
	return res

def get_by_machinesid(domaind, machinesid):
	db = current_app.db
	shares = []
	for res in db.session.query(NetShare).filter_by(machine_sid = machinesid).filter(NetShare.ad_id == domainid):
		shares.append(res.to_dict())
	
	return shares

def list_interesting(domainid):
	default_shares = ['print$','IPC$','ADMIN$', 'SYSVOL', 'NETLOGON']
	for x in string.ascii_uppercase:
		default_shares.append('%s$' % x)
	db = current_app.db
	shares = []
	q = db.session.query(NetShare)\
		.filter_by(ad_id = domainid)\
		.filter(NetShare.netname.notin_(default_shares))
	for share in q.all():
		shares.append(share.to_dict())
	
	return shares