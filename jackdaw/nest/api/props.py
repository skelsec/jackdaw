from flask import current_app
from jackdaw.dbmodel.adobjprops import JackDawADObjProps

def set_hvt(graphid, oid):
	p = JackDawADObjProps()
	p.prop = 'HVT'
	p.oid = oid
	p.graph_id = int(graphid)
	current_app.db.session.add(p)
	current_app.db.session.commit()

def clear_hvt(graphid, oid):
	for res in current_app.db.session.query(JackDawADObjProps).filter_by(oid = oid).filter(JackDawADObjProps.prop == 'HVT').filter(JackDawADObjProps.graph_id == graphid).all():
		current_app.db.session.delete(res)
		current_app.db.session.commit()

def set_owned(graphid, oid):
	p = JackDawADObjProps()
	p.prop = 'OWNED'
	p.oid = oid
	p.graph_id = int(graphid)
	current_app.db.session.add(p)
	current_app.db.session.commit()

def clear_owned(graphid, oid):
	for res in current_app.db.session.query(JackDawADObjProps).filter_by(oid = oid).filter(JackDawADObjProps.prop == 'OWNED').filter(JackDawADObjProps.graph_id == graphid).all():
		current_app.db.session.delete(res)
		current_app.db.session.commit()