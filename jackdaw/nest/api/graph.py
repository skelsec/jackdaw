#!/usr/bin/env python3
#
# Author:
#  Tamas Jos (@skelsec)
#

# System modules
import datetime
import tempfile
import os
import pathlib
import copy
import threading

from jackdaw.dbmodel.graphinfo import GraphInfo, GraphInfoAD
from jackdaw.nest.graph.domain import DomainGraph
from jackdaw.nest.graph.graphdata import GraphData
from jackdaw.nest.graph.construct import GraphConstruct
from jackdaw.nest.graph.domaindiff import DomainDiff
from jackdaw.dbmodel.adgroup import Group
from jackdaw.dbmodel.edgelookup import EdgeLookup
from jackdaw.dbmodel.edge import Edge
from jackdaw.dbmodel.aduser import ADUser
from jackdaw.dbmodel.adinfo import ADInfo
from jackdaw.dbmodel.adcomp import Machine
from jackdaw.dbmodel.adou import ADOU
from jackdaw.dbmodel.adobjprops import ADObjProps
from jackdaw import logger
import connexion
from sqlalchemy import or_


# 3rd party modules
from flask import make_response, abort, current_app, send_file, after_this_request


graph_id_ctr = 1
graphs = {}

diff_id_ctr = 1
diffs = {}

def __exclude_parse(exclude):
	#sadly connexion is not capable to do this by itself
	res = []
	if exclude is None:
		return res
	for p in exclude.split(','):
		res.append(p.strip())
	
	return res

def list_graphs():
	t = []
	graph_cache_dir = current_app.config['JACKDAW_WORK_DIR'].joinpath('graphcache')
	x = [f for f in graph_cache_dir.iterdir() if f.is_dir()]
	for d in x:
		t.append(int(str(d.name)))
	return t

def create(adids):
	if len(adids) != 1:
		logger.warning('More than one adid requested, but only one is supported currently!')
	
	sqlite_file = None
	if current_app.config['SQLALCHEMY_DATABASE_URI'].lower().startswith('sqlite') is True:
		sqlite_file = current_app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')

	logger.error(sqlite_file)
	for ad_id in adids:
		domaininfo = current_app.db.session.query(ADInfo).get(ad_id)
		domain_sid = domaininfo.objectSid
		domain_id = domaininfo.id

		res = current_app.db.session.query(GraphInfoAD).filter_by(ad_id = ad_id).first()

		gi = current_app.db.session.query(GraphInfo).get(res.graph_id)
		graphid = gi.id
		graph_cache_dir = current_app.config['JACKDAW_WORK_DIR'].joinpath('graphcache')
		graph_dir = graph_cache_dir.joinpath(str(gi.id))
		try:
			graph_dir.mkdir(parents=True, exist_ok=False)
		except Exception as e:
			logger.warning('Graph cache dir with ID %s already exists, skipping! Err %s' % (str(gi.id), str(e)))
			continue
			
		current_app.config.get('JACKDAW_GRAPH_BACKEND_OBJ').create(current_app.db.session, str(gi.id), graph_dir, sqlite_file = sqlite_file)
	
	#TODO: fix this, need noew UI to handle the logic :(
	return {'graphid' : graphid}

def delete(graphid):
	del current_app.config['JACKDAW_GRAPH_DICT'][graphid]
	return {}


def save(graphid):
	raise Exception('Not yet implemented!')
	#with tempfile.NamedTemporaryFile(delete=False) as tmpfile:
	#	temp_file_name = tmpfile.name
	#
	##logger.debug('Temp file created, but will not be removed! %s' % temp_file_name)
	#current_app.config['JACKDAW_GRAPH_DICT'][graphid].to_gzip(temp_file_name)
	#
	#attachment_name = 'graph_%s_%s.gzip' % (graphid, datetime.datetime.now().isoformat())
	#resp = send_file(temp_file_name,
	#	as_attachment=True, 
	#	mimetype='application/octet-stream',
	#	attachment_filename=attachment_name
	#)
	#return resp

def upload(file_to_upload):
	pass
	#global graph_id_ctr
	#old_graph_id_ctr = graph_id_ctr
	#graph_id_ctr += 1
	#
	#file_to_upload = connexion.request.files['file_to_upload']
	#graphs[old_graph_id_ctr] = DomainGraph.from_gzip_stream(file_to_upload.stream)
	#graphs[old_graph_id_ctr].dbsession = current_app.db.session #need to restore db session
	#
	#return {'graphid' : old_graph_id_ctr}

def load(graphid):
	if graphid not in current_app.config['JACKDAW_GRAPH_DICT']:
		if graphid not in current_app.config['JACKDAW_GRAPH_DICT_LOADING']:
			current_app.config['JACKDAW_GRAPH_DICT_LOADING'][graphid] = threading.Event()
			graphid = int(graphid)
			current_app.config['JACKDAW_WORK_DIR']
			graph_cache_dir = current_app.config['JACKDAW_WORK_DIR'].joinpath('graphcache')
			graph_dir = graph_cache_dir.joinpath(str(graphid))
			if graph_dir.exists() is False:
				current_app.config['JACKDAW_GRAPH_DICT_LOADING'][graphid].set()
				raise Exception('Graph cache dir doesnt exists!')
			else:
				current_app.config['JACKDAW_GRAPH_DICT'][graphid] = current_app.config.get('JACKDAW_GRAPH_BACKEND_OBJ').load(current_app.db.session, graphid, graph_dir)
				current_app.config['JACKDAW_GRAPH_DICT_LOADING'][graphid].set()
				return graphid
		else:
			current_app.config['JACKDAW_GRAPH_DICT_LOADING'][graphid].wait()
			return graphid
	else:
		return graphid

def get(graphid):
	if graphid not in current_app.config['JACKDAW_GRAPH_DICT']:
		load(graphid)

	res = current_app.config['JACKDAW_GRAPH_DICT'][graphid].all_shortest_paths()
	return res.to_dict()

def getdomainsids(graphid):
	if graphid not in current_app.config['JACKDAW_GRAPH_DICT']:
		load(graphid)

	dsids = []
	for domain_id in current_app.config['JACKDAW_GRAPH_DICT'][graphid].adids:
		adinfo = current_app.db.session.query(ADInfo).get(domain_id)
		dsids.append(adinfo.objectSid)
	
	return dsids

def getdomainids(graphid):
	if graphid not in current_app.config['JACKDAW_GRAPH_DICT']:
		load(graphid)
	
	return current_app.config['JACKDAW_GRAPH_DICT'][graphid].adids


def query_path(graphid, src = None, dst = None, exclude = None, format = 'd3', maxhops = None):
	allshrotest = False
	pathonly = False
	if format.lower() == 'path':
		pathonly = True

	exclude_edgetypes = __exclude_parse(exclude)
	if graphid not in current_app.config['JACKDAW_GRAPH_DICT']:
		load(graphid)
	if src == '':
		src = None
	if dst == '':
		dst = None
	if maxhops is None or maxhops == '':
		maxhops = None
	else:
		maxhops = int(maxhops)
		if maxhops < 2:
			maxhops = 2
	if src is None and dst is None:
		return {}
	res = current_app.config['JACKDAW_GRAPH_DICT'][graphid].shortest_paths(src, dst, exclude = exclude_edgetypes, pathonly = pathonly, maxhops = maxhops, all_shortest = allshrotest)
	if pathonly is True:
		return res
	return res.to_dict(format = format)

def query_path_da(graphid, exclude = None, format = 'vis'):
	if graphid not in current_app.config['JACKDAW_GRAPH_DICT']:
		load(graphid)
	pathonly = False
	if format.lower() == 'path':
		pathonly = True
	
	exclude_edgetypes = __exclude_parse(exclude)
	da_sids = {}
	
	for domain_id in current_app.config['JACKDAW_GRAPH_DICT'][graphid].adids:
		for res in current_app.db.session.query(Group).filter_by(ad_id = domain_id).filter(Group.objectSid.like('%-512')).all():
			da_sids[res.objectSid] = 0
	
	if len(da_sids) == 0:
		return 'No domain administrator group found', 404
	
	res = GraphData()
	if pathonly is True:
		res = []
	for sid in da_sids:
		res += current_app.config['JACKDAW_GRAPH_DICT'][graphid].shortest_paths(None, sid, exclude = exclude_edgetypes, pathonly=pathonly)


	#print(res)
	return res.to_dict(format = format)

def query_path_dcsync(graphid, exclude = None, format = 'vis'):
	exclude_edgetypes = __exclude_parse(exclude)
	if graphid not in current_app.config['JACKDAW_GRAPH_DICT']:
		load(graphid)

	res = GraphData()
	res += current_app.config['JACKDAW_GRAPH_DICT'][graphid].get_dcsync()

	return res.to_dict(format = format)

def query_path_kerberoastda(graphid, exclude = None, format = 'vis'):
	exclude_edgetypes = __exclude_parse(exclude)
	if graphid not in current_app.config['JACKDAW_GRAPH_DICT']:
		load(graphid)

	target_sids = {}
	da_sids = {}

	for domain_id in current_app.config['JACKDAW_GRAPH_DICT'][graphid].adids:
		for res in current_app.db.session.query(Group).filter_by(ad_id = domain_id).filter(Group.objectSid.like('%-512')).all():
			da_sids[res.objectSid] = 0

		for res in current_app.db.session.query(ADUser.objectSid)\
			.filter_by(ad_id = domain_id)\
			.filter(ADUser.servicePrincipalName != None).all():
			
			target_sids[res[0]] = 0

	res = GraphData()
	for dst_sid in da_sids:
		for src_sid in target_sids:
			res += current_app.config['JACKDAW_GRAPH_DICT'][graphid].shortest_paths(src_sid, dst_sid, exclude = exclude_edgetypes)

	return res.to_dict(format = format)

def query_path_kerberoastany(graphid, exclude = None, format = 'vis'):
	exclude_edgetypes = __exclude_parse(exclude)
	if graphid not in current_app.config['JACKDAW_GRAPH_DICT']:
		load(graphid)

	target_sids = {}
	domain_sids = {}
	path_to_da = []

	for domain_id in current_app.config['JACKDAW_GRAPH_DICT'][graphid].adids:
		res = current_app.db.session.query(ADInfo).get(domain_id)
		domain_sids[res.objectSid] = 1

		for res in current_app.db.session.query(ADUser.objectSid)\
			.filter_by(ad_id = domain_id)\
			.filter(ADUser.servicePrincipalName != None).all():
			
			target_sids[res[0]] = 0

	res = GraphData()
	for src_sid in target_sids:
		for domain_sid in domain_sids:
			if current_app.config['JACKDAW_GRAPH_DICT'][graphid].has_path(src_sid, domain_sid) is False:
				res += current_app.config['JACKDAW_GRAPH_DICT'][graphid].shortest_paths(src_sid=src_sid, dst_sid = None, exclude = exclude_edgetypes)
			else:
				path_to_da.append(src_sid)

	#TODO: send the path_to_da as well!
	return res.to_dict(format = format)

def query_path_asreproast(graphid, exclude=None, format = 'vis'):
	exclude_edgetypes = __exclude_parse(exclude)
	if graphid not in current_app.config['JACKDAW_GRAPH_DICT']:
		load(graphid)

	target_sids = {}
	da_sids = {}

	for domain_id in current_app.config['JACKDAW_GRAPH_DICT'][graphid].adids:
		for res in current_app.db.session.query(Group).filter_by(ad_id = domain_id).filter(Group.objectSid.like('%-512')).all():
			da_sids[res.objectSid] = 0

		for res in current_app.db.session.query(ADUser.objectSid)\
			.filter_by(ad_id = domain_id)\
			.filter(ADUser.UAC_DONT_REQUIRE_PREAUTH == True).all():
			
			target_sids[res[0]] = 0

	res = GraphData()
	for dst_sid in da_sids:
		for src_sid in target_sids:
			res += current_app.config['JACKDAW_GRAPH_DICT'][graphid].shortest_paths(src_sid, dst_sid, exclude = exclude_edgetypes)

	return res.to_dict(format = format)

def query_path_tohighvalue(graphid, exclude = None, format = 'vis'):
	exclude_edgetypes = __exclude_parse(exclude)
	if graphid not in current_app.config['JACKDAW_GRAPH_DICT']:
		load(graphid)

	target_sids = {}

	for domain_id in current_app.config['JACKDAW_GRAPH_DICT'][graphid].adids:
		for res in current_app.db.session.query(EdgeLookup.oid)\
			.filter_by(ad_id = domain_id)\
			.filter(EdgeLookup.oid == ADObjProps.oid)\
			.filter(ADObjProps.graph_id == graphid)\
			.filter(ADObjProps.prop == 'HVT')\
			.all():
			
			target_sids[res[0]] = 0

	res = GraphData()
	for dst_sid in target_sids:
		res += current_app.config['JACKDAW_GRAPH_DICT'][graphid].shortest_paths(dst_sid=dst_sid, ignore_notfound = True, exclude = exclude_edgetypes)
		
	return res.to_dict(format = format)

def query_path_ownedda(graphid, exclude = None, format = 'vis'):
	exclude_edgetypes = __exclude_parse(exclude)
	if graphid not in current_app.config['JACKDAW_GRAPH_DICT']:
		load(graphid)

	target_sids = {}
	da_sids = {}

	for domain_id in current_app.config['JACKDAW_GRAPH_DICT'][graphid].adids:
		for res in current_app.db.session.query(Group).filter_by(ad_id = domain_id).filter(Group.objectSid.like('%-512')).all():
			da_sids[res.objectSid] = 0


		for res in current_app.db.session.query(EdgeLookup.oid)\
			.filter_by(ad_id = domain_id)\
			.filter(EdgeLookup.oid == ADObjProps.oid)\
			.filter(ADObjProps.graph_id == graphid)\
			.filter(ADObjProps.prop == 'OWNED')\
			.all():
			
			target_sids[res[0]] = 0

	res = GraphData()
	for dst_sid in da_sids:
		for src_sid in target_sids:
			res += current_app.config['JACKDAW_GRAPH_DICT'][graphid].shortest_paths(src_sid, dst_sid, exclude = exclude_edgetypes)

	return res.to_dict(format = format)

def query_path_fromowned(graphid, exclude = None, format = 'vis'):
	exclude_edgetypes = __exclude_parse(exclude)
	if graphid not in current_app.config['JACKDAW_GRAPH_DICT']:
		load(graphid)

	target_sids = {}

	for domain_id in current_app.config['JACKDAW_GRAPH_DICT'][graphid].adids:
		for res in current_app.db.session.query(EdgeLookup.oid)\
			.filter_by(ad_id = domain_id)\
			.filter(EdgeLookup.oid == ADObjProps.oid)\
			.filter(ADObjProps.graph_id == graphid)\
			.filter(ADObjProps.prop == 'OWNED')\
			.all():
			
			target_sids[res[0]] = 0

	res = GraphData()
	for src_sid in target_sids:
		res += current_app.config['JACKDAW_GRAPH_DICT'][graphid].shortest_paths(src_sid=src_sid, exclude = exclude_edgetypes)

	return res.to_dict(format = format)

def query_path_fromowned_tohighvalue(graphid, exclude = None, format = 'vis'):
	exclude_edgetypes = __exclude_parse(exclude)
	if graphid not in current_app.config['JACKDAW_GRAPH_DICT']:
		load(graphid)

	source_sids = {}

	for domain_id in current_app.config['JACKDAW_GRAPH_DICT'][graphid].adids:
		for res in current_app.db.session.query(EdgeLookup.oid)\
			.filter_by(ad_id = domain_id)\
			.filter(EdgeLookup.oid == ADObjProps.oid)\
			.filter(ADObjProps.graph_id == graphid)\
			.filter(ADObjProps.prop == 'OWNED')\
			.all():
			
			source_sids[res[0]] = 0

	target_sids = {}

	for domain_id in current_app.config['JACKDAW_GRAPH_DICT'][graphid].adids:
		for res in current_app.db.session.query(EdgeLookup.oid)\
			.filter_by(ad_id = domain_id)\
			.filter(EdgeLookup.oid == ADObjProps.oid)\
			.filter(ADObjProps.graph_id == graphid)\
			.filter(ADObjProps.prop == 'HVT')\
			.all():
			
			target_sids[res[0]] = 0

	res = GraphData()
	for src_sid in source_sids:
		for dst_sid in target_sids:
			res += current_app.config['JACKDAW_GRAPH_DICT'][graphid].shortest_paths(src_sid=src_sid, dst_sid=dst_sid, exclude = exclude_edgetypes)

	return res.to_dict(format = format)


def list_nodes(graphid, with_data = False):
	if graphid not in current_app.config['JACKDAW_GRAPH_DICT']:
		return 'Graph Not Found', 404
	nodes = []
	for node in current_app.config['JACKDAW_GRAPH_DICT'][graphid].get_node():
		nodes.append(node.to_dict())
	return nodes

def get_node(graphid, nodeid):
	if graphid not in current_app.config['JACKDAW_GRAPH_DICT']:
		return 'Graph Not Found', 404
	return current_app.config['JACKDAW_GRAPH_DICT'][graphid].get_node(nodeid)

def query_path_all(graphid):
	if graphid not in current_app.config['JACKDAW_GRAPH_DICT']:
		return 'Graph Not Found', 404
	return current_app.config['JACKDAW_GRAPH_DICT'][graphid].show_all().to_dict(format = 'vis')

#def search_sid(graphid, oid):
	#for domain_id in current_app.config['JACKDAW_GRAPH_DICT'][graphid].adids:

def search(graphid, text):
	if graphid not in current_app.config['JACKDAW_GRAPH_DICT']:
		load(graphid)

	if len(text) < 3:
		return 'Search term too short!', 404
	
	results = []

	def create_element(sid, name, otype, adid):
		return {
			'sid' : sid,
			'otype' : otype,
			'adid' : adid,
			'text' : name,
			'owned' : False,
			'highvalue' : False,
		}

	#search users
	for domain_id in current_app.config['JACKDAW_GRAPH_DICT'][graphid].adids:
		term = "%%%s%%" % text
		qry_user_name = current_app.db.session.query(ADUser.sAMAccountName, ADUser.objectSid).filter_by(ad_id = domain_id).filter(ADUser.sAMAccountName.ilike(term)).limit(5)
		for username, sid in qry_user_name.all():
			results.append(create_element(sid, username, 'user', domain_id))
		
		qry_user_sid = current_app.db.session.query(ADUser.sAMAccountName, ADUser.objectSid).filter_by(ad_id = domain_id).filter(ADUser.objectSid.ilike(term)).limit(5)
		for username, sid in qry_user_sid.all():
			results.append(create_element(sid, username, 'user', domain_id))


		qry_machine_name = current_app.db.session.query(Machine.sAMAccountName, Machine.objectSid).filter_by(ad_id = domain_id).filter(Machine.sAMAccountName.ilike(term)).limit(5)
		for username, sid in qry_machine_name.all():
			results.append(create_element(sid, username, 'machine', domain_id))

		qry_machine_sid = current_app.db.session.query(Machine.sAMAccountName, Machine.objectSid).filter_by(ad_id = domain_id).filter(Machine.objectSid.ilike(term)).limit(5)
		for username, sid in qry_machine_sid.all():
			results.append(create_element(sid, username, 'machine', domain_id))
		

		qry_group_name = current_app.db.session.query(Group.sAMAccountName, Group.objectSid).filter_by(ad_id = domain_id).filter(Group.sAMAccountName.ilike(term)).limit(5)
		for username, sid in qry_group_name.all():
			results.append(create_element(sid, username, 'group', domain_id))

		qry_group_sid = current_app.db.session.query(Group.sAMAccountName, Group.objectSid).filter_by(ad_id = domain_id).filter(Group.objectSid.ilike(term)).limit(5)
		for username, sid in qry_group_sid.all():
			results.append(create_element(sid, username, 'group', domain_id))


		qry_ou_name = current_app.db.session.query(ADOU.name, ADOU.objectGUID).filter_by(ad_id = domain_id).filter(ADOU.name.ilike(term)).limit(5)
		for username, sid in qry_ou_name.all():
			results.append(create_element(sid, username, 'ou', domain_id))

		qry_ou_sid = current_app.db.session.query(ADOU.name, ADOU.objectGUID).filter_by(ad_id = domain_id).filter(ADOU.objectGUID.ilike(term)).limit(5)
		for username, sid in qry_ou_sid.all():
			results.append(create_element(sid, username, 'ou', domain_id))
		
		for res in results:
			qry_props = current_app.db.session.query(ADObjProps).filter_by(oid = res['sid']).filter(ADObjProps.graph_id == graphid)
			for qr in qry_props.all():
				if qr.prop == 'HVT':
					res['highvalue'] = True
				if qr.prop == 'OWNED':
					res['owned'] = True

	return results


def get_members(graphid, sid, maxhops = 1, format = 'vis'):
	if graphid not in current_app.config['JACKDAW_GRAPH_DICT']:
		load(graphid)
	
	res = GraphData()
	res += current_app.config['JACKDAW_GRAPH_DICT'][graphid].get_members(sid, maxhops)

	return res.to_dict(format = 'vis')


def stat_distance(graphid, sid):
	if graphid not in current_app.config['JACKDAW_GRAPH_DICT']:
		load(graphid)

	distances = current_app.config['JACKDAW_GRAPH_DICT'][graphid].distances_from_node(sid)
	
	return distances

def diff(graphids):
	global diff_id_ctr
	
	db = current_app.db
	dd = DomainDiff(dbsession=db.session)
	construct_old = GraphConstruct(graphids['src'])
	construct_new = GraphConstruct(graphids['dst'])

	diffs[diff_id_ctr] = dd
	diff_id_ctr += 1

	dd.construct(construct_old, construct_new)

	return {
		'diffid' : diff_id_ctr - 1
	}

def list_diff_all():
	return list(diffs.keys())

def diff_nodes(diffid):
	diffres = diffs[diffid].diff_nodes()
	return diffres

def diff_path_distance(diffid, sid):
	diffres = diffs[diffid].diff_path_distance(sid)
	return diffres

def diff_path(diffid, srcsid, dstsid):
	diffres = diffs[diffid].diff_path(srcsid, dstsid)
	return diffres

def diff_path_da(diffid):
	diffres = diffs[diffid].diff_path_da()
	return diffres