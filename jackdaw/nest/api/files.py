
from flask import current_app
from jackdaw.dbmodel.netfile import NetFile
from jackdaw.dbmodel.netshare import NetShare
from jackdaw.dbmodel.netdacl import NetDACL
from jackdaw.dbmodel.netdir import NetDir
from jackdaw.dbmodel.adcomp import Machine


def get_file(domainid, fileid):
	db = current_app.db
	f = db.session.query(NetFile).get(fileid)
	return f.to_dict()

def get_dir(domainid, dirid):
	db = current_app.db
	f = db.session.query(NetDir).get(dirid)
	return f.to_dict()

def search_file_name(domainid, pattern, page, maxcnt):
	db = current_app.db
	pattern = pattern['pattern']
	res = {
		'res' : [],
		'page': {},
	}

	qry = db.session.query(
		NetFile.id, NetFile.name, NetFile.unc
		).filter(NetShare.machine_sid == Machine.objectSid
		).filter(Machine.ad_id == domainid
		).filter(NetDir.share_id == NetShare.id
		).filter(NetDir.id == NetFile.folder_id
		).filter(NetFile.name.like(pattern))

	files = []
	qry = qry.paginate(page = page, max_per_page = maxcnt)
	for fid, name, unc in qry.items:
		files.append({
			'id' : fid,
			'name' : name,
			'unc' : unc,    
		})

	page = dict(
		total=qry.total, 
		current_page=qry.page,
		per_page=qry.per_page
	)

	res['res'] = files
	res['page'] = page

	return res

def search_file_ext(domainid, pattern, page, maxcnt):
	db = current_app.db
	pattern = pattern['pattern']
	res = {
		'res' : [],
		'page': {},
	}

	qry = db.session.query(
		NetFile.id, NetFile.name, NetFile.unc
		).filter(NetShare.machine_id == Machine.id
		).filter(Machine.ad_id == domainid
		).filter(NetDir.share_id == NetShare.id
		).filter(NetDir.id == NetFile.folder_id
		).filter(NetFile.ext.like(pattern))

	files = []
	qry = qry.paginate(page = page, max_per_page = maxcnt)
	for fid, name, unc in qry.items:
		files.append({
			'id' : fid,
			'name' : name,
			'unc' : unc,    
		})

	page = dict(
		total=qry.total, 
		current_page=qry.page,
		per_page=qry.per_page
	)

	res['res'] = files
	res['page'] = page

	return res

def search_file_full(domainid, filter, page, maxcnt):
	db = current_app.db
	pattern = filter['pattern']
	ownersid = filter.get('ownersid')
	machineid = filter.get('machineid')
	size_greather = filter.get('size_greather')
	size_smaller = filter.get('size_smaller')
	created_after = filter.get('created_after')
	created_before = filter.get('created_before')
	changed_after = filter.get('changed_after')
	changed_before = filter.get('changed_before')
	ext_pattern = filter.get('extension_pattern')
	
	res = {
		'res' : [],
		'page': {},
	}

	qry = db.session.query(
		NetFile.id, NetFile.name, NetFile.unc
		).filter(NetShare.machine_id == Machine.id
		).filter(Machine.ad_id == domainid
		).filter(NetDir.share_id == NetShare.id
		).filter(NetDir.id == NetFile.folder_id
		).filter(NetFile.unc.like(pattern))

	if ownersid is not None:
		qry = qry.filter(NetDACL.object_id == NetFile.id
			).filter(NetDACL.owner_sid == ownersid
			)

	if machineid is not None:
		qry = qry.filter(Machine.id == machineid)

	if created_after is not None:
		qry = qry.filter(NetFile.creation_time >= created_after)
	
	if created_after is not None:
		qry = qry.filter(NetFile.creation_time <= created_before)
	
	if changed_after is not None:
		qry = qry.filter(NetFile.change_time >= changed_after)
	
	if changed_before is not None:
		qry = qry.filter(NetFile.change_time <= changed_before)
	
	if size_greather is not None:
		qry = qry.filter(NetFile.size >= size_greather)
	
	if size_smaller is not None:
		qry = qry.filter(NetFile.size <= size_smaller)
	
	if ext_pattern is not None:
		qry = qry.filter(NetFile.ext.like(ext_pattern))


	files = []
	qry = qry.paginate(page = page, max_per_page = maxcnt)
	for fid, name, unc in qry.items:
		files.append({
			'id' : fid,
			'name' : name,
			'unc' : unc,    
		})

	page = dict(
		total=qry.total, 
		current_page=qry.page,
		per_page=qry.per_page
	)

	res['res'] = files
	res['page'] = page

	return res

def search_file_owner(domainid, ownersid, pattern, page, maxcnt):
	db = current_app.db
	pattern = pattern['pattern']
	res = {
		'res' : [],
		'page': {},
	}

	qry = db.session.query(
		NetFile.id, NetFile.name, NetFile.unc
		).filter(NetShare.machine_id == Machine.id
		).filter(Machine.ad_id == domainid
		).filter(NetDir.share_id == NetShare.id
		).filter(NetDir.id == NetFile.folder_id
		).filter(NetDACL.object_id == NetFile.id
		).filter(NetDACL.owner_sid == ownersid
		).filter(NetFile.unc.like(pattern))

	files = []
	qry = qry.paginate(page = page, max_per_page = maxcnt)
	for fid, name, unc in qry.items:
		files.append({
			'id' : fid,
			'name' : name,
			'unc' : unc,    
		})

	page = dict(
		total=qry.total, 
		current_page=qry.page,
		per_page=qry.per_page
	)

	res['res'] = files
	res['page'] = page

	return res