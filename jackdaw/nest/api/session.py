
from jackdaw.dbmodel.netsession import NetSession
from jackdaw.dbmodel.adcomp import Machine
from jackdaw.dbmodel.aduser import ADUser
from flask import current_app

def session_list(domainid):
	db = current_app.db
	sessions = {}
	for mid, mname, session in db.session.query(Machine.id, Machine.sAMAccountName, NetSession).filter(Machine.ad_id == domainid).filter(NetSession.machine_id == Machine.id).distinct(NetSession.username):
		if mid not in sessions:
			sessions[mid] = {}
			sessions[mid]['sessions'] = []

		sessions[mid]['machinename'] = mname
		sessions[mid]['sessions'].append(session.username)

	return sessions

def session_add(domainid, session):
	db = current_app.db
	print(session)
	cname = session['hostname']
	if cname[-1] != '$':
		cname = session['hostname'] + '$'
	comp = db.session.query(Machine.id, Machine.sAMAccountName).filter_by(ad_id = domainid).filter(Machine.sAMAccountName == cname).first()
	if comp is None:
		return 'Machine not found!', 404
	uname = session['username']
	user = db.session.query(ADUser.sAMAccountName).filter_by(ad_id = domainid).filter(ADUser.sAMAccountName == uname).first()
	if user is None:
		return 'User not found!', 404

	sess = NetSession()
	sess.machine_id = comp.id
	sess.source = comp.sAMAccountName
	sess.username = user.sAMAccountName
	try:
		db.session.add(sess)
		db.session.commit()
	except:
		db.session.rollback()

	return 'Session created!', 200
