from flask import current_app
from jackdaw.dbmodel.netshare import NetShare

def get_machineid(machineid):
	db = current_app.db
	shares = []
	for share in db.session.query(NetShare).filter_by(machine_id = machineid).all():
		print(share)
		shares.append(share.to_dict())
	
	return shares

