from flask import current_app
from jackdaw.dbmodel.adobjprops import ADObjProps

def set_hvt(graphid, oid):
	p = ADObjProps()
	p.prop = 'HVT'
	p.oid = oid
	p.graph_id = int(graphid)
	current_app.db.session.add(p)
	current_app.db.session.commit()

def clear_hvt(graphid, oid):
	for res in current_app.db.session.query(ADObjProps).filter_by(oid = oid).filter(ADObjProps.prop == 'HVT').filter(ADObjProps.graph_id == graphid).all():
		current_app.db.session.delete(res)
		current_app.db.session.commit()

def set_owned(graphid, oid):
	p = ADObjProps()
	p.prop = 'OWNED'
	p.oid = oid
	p.graph_id = int(graphid)
	current_app.db.session.add(p)
	current_app.db.session.commit()

def clear_owned(graphid, oid):
	for res in current_app.db.session.query(ADObjProps).filter_by(oid = oid).filter(ADObjProps.prop == 'OWNED').filter(ADObjProps.graph_id == graphid).all():
		current_app.db.session.delete(res)
		current_app.db.session.commit()