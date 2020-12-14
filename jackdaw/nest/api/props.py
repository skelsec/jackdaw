from flask import current_app
from jackdaw.dbmodel.adobjprops import ADObjProps

def set_hvt(graphid, oid):
	p = ADObjProps(int(graphid), oid, 'HVT')
	current_app.db.session.add(p)
	current_app.db.session.commit()

def clear_hvt(graphid, oid):
	for res in current_app.db.session.query(ADObjProps).filter_by(oid = oid).filter(ADObjProps.prop == 'HVT').filter(ADObjProps.graph_id == graphid).all():
		current_app.db.session.delete(res)
		current_app.db.session.commit()

def set_owned(graphid, oid):
	print('set_owned!')
	p = ADObjProps(int(graphid), oid, 'OWNED')
	current_app.db.session.add(p)
	current_app.db.session.commit()

def clear_owned(graphid, oid):
	print('clear_owned!')
	for res in current_app.db.session.query(ADObjProps).filter_by(oid = oid).filter(ADObjProps.prop == 'OWNED').filter(ADObjProps.graph_id == graphid).all():
		current_app.db.session.delete(res)
		current_app.db.session.commit()