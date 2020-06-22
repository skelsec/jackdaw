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

from jackdaw.dbmodel.graphinfo import GraphInfo
from jackdaw.nest.graph.domain import DomainGraph
from jackdaw.nest.graph.graphdata import GraphData
from jackdaw.nest.graph.construct import GraphConstruct
from jackdaw.nest.graph.domaindiff import DomainDiff
from jackdaw.dbmodel.adgroup import Group
from jackdaw.dbmodel.edgelookup import EdgeLookup
from jackdaw.dbmodel.edge import Edge
from jackdaw.dbmodel.aduser import ADUser
from jackdaw.dbmodel.adinfo import ADInfo
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
	for ad_id in adids:
		domaininfo = current_app.db.session.query(ADInfo).get(ad_id)
		domain_sid = domaininfo.objectSid
		domain_id = domaininfo.id


		for gi in current_app.db.session.query(GraphInfo).filter_by(ad_id = domain_id).all():
			graphid = gi.id
			graph_cache_dir = current_app.config['JACKDAW_WORK_DIR'].joinpath('graphcache')
			graph_dir = graph_cache_dir.joinpath(str(gi.id))
			try:
				graph_dir.mkdir(parents=True, exist_ok=False)
			except Exception as e:
				logger.warning('Graph cache dir with ID %s already exists, skipping! Err %s' % (str(gi.id), str(e)))
				continue
			
			current_app.config.get('JACKDAW_GRAPH_BACKEND_OBJ').create(current_app.db.session, domain_id, str(gi.id), graph_dir)
	
	#TODO: fix this, need noew UI to handle the logic :(
	return {'graphid' : graphid}

def delete(graphid):
	del graphs[graphid]
	return {}


def save(graphid):
	raise Exception('Not yet implemented!')
	#with tempfile.NamedTemporaryFile(delete=False) as tmpfile:
	#	temp_file_name = tmpfile.name
	#
	##logger.debug('Temp file created, but will not be removed! %s' % temp_file_name)
	#graphs[graphid].to_gzip(temp_file_name)
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
	graphid = int(graphid)
	current_app.config['JACKDAW_WORK_DIR']
	graph_cache_dir = current_app.config['JACKDAW_WORK_DIR'].joinpath('graphcache')
	graph_dir = graph_cache_dir.joinpath(str(graphid))
	if graph_dir.exists() is False:
		raise Exception('Graph cache dir doesnt exists!')
	else:
		graphs[graphid] = current_app.config.get('JACKDAW_GRAPH_BACKEND_OBJ').load(current_app.db.session, graphid, graph_dir)
		
		return {'graphid' : graphid}

def get(graphid):
	if graphid not in graphs:
		return 'Graph Not Found', 404
	res = graphs[graphid].all_shortest_paths()
	return res.to_dict()

def query_path(graphid, src = None, dst = None, format = 'd3'):
	if graphid not in graphs:
		load(graphid)
	if src == '':
		src = None
	if dst == '':
		dst = None
	if src is None and dst is None:
		return {}
	res = graphs[graphid].shortest_paths(src, dst)
	return res.to_dict(format = format)

def query_path_da(graphid, format = 'vis'):
	if graphid not in graphs:
		load(graphid)
	
	da_sids = {}
	#searching for domain admin SID
	
	#for node in graphs[graphid].get_node():
	#	print(node)
	#	if node.id == graphs[graphid].domain_sid + '-512':
	#		da_sids[node.id] = 1
	print(graphs[graphid].domain_id)
	for res in current_app.db.session.query(Group).filter_by(ad_id = graphs[graphid].domain_id).filter(Group.objectSid.like('%-512')).all():
		da_sids[res.objectSid] = 0
	
	if len(da_sids) == 0:
		return 'No domain administrator group found', 404
	
	res = GraphData()
	for sid in da_sids:
		res += graphs[graphid].shortest_paths(None, sid)


	#print(res)
	return res.to_dict(format = format)

def query_path_dcsync(graphid, format = 'vis'):
	if graphid not in graphs:
		load(graphid)

	target_sids = {}
	da_sids = {graphs[graphid].domain_sid : 0}

	for res in current_app.db.session.query(EdgeLookup.oid)\
		.filter_by(ad_id = graphs[graphid].domain_id)\
		.filter(EdgeLookup.id == Edge.src)\
		.filter(EdgeLookup.oid != None)\
		.filter(or_(Edge.label == 'GetChanges', Edge.label == 'GetChangesAll'))\
		.all():
		
		target_sids[res[0]] = 0

	res = GraphData()
	for dst_sid in da_sids:
		for src_sid in target_sids:
			res += graphs[graphid].shortest_paths(src_sid, dst_sid)

	return res.to_dict(format = format)

def query_path_kerberoastda(graphid, format = 'vis'):
	if graphid not in graphs:
		load(graphid)

	target_sids = {}
	da_sids = {}

	for res in current_app.db.session.query(Group).filter_by(ad_id = graphs[graphid].domain_id).filter(Group.objectSid.like('%-512')).all():
		da_sids[res.objectSid] = 0

	for res in current_app.db.session.query(ADUser.objectSid)\
		.filter_by(ad_id = graphs[graphid].domain_id)\
		.filter(ADUser.servicePrincipalName != None).all():
		
		target_sids[res[0]] = 0

	res = GraphData()
	for dst_sid in da_sids:
		for src_sid in target_sids:
			res += graphs[graphid].shortest_paths(src_sid, dst_sid)

	return res.to_dict(format = format)

def query_path_kerberoastany(graphid, format = 'vis'):
	if graphid not in graphs:
		load(graphid)

	target_sids = {}
	path_to_da = []

	for res in current_app.db.session.query(ADUser.objectSid)\
		.filter_by(ad_id = graphs[graphid].domain_id)\
		.filter(ADUser.servicePrincipalName != None).all():
		
		target_sids[res[0]] = 0

	res = GraphData()
	for src_sid in target_sids:
		if graphs[graphid].has_path(src_sid, graphs[graphid].domain_sid) is False:
			res += graphs[graphid].shortest_paths(src_sid=src_sid, dst_sid = None)
		else:
			path_to_da.append(src_sid)

	#TODO: send the path_to_da as well!
	return res.to_dict(format = format)

def query_path_asreproast(graphid, format = 'vis'):
	if graphid not in graphs:
		load(graphid)

	target_sids = {}
	da_sids = {}

	for res in current_app.db.session.query(Group).filter_by(ad_id = graphs[graphid].domain_id).filter(Group.objectSid.like('%-512')).all():
		da_sids[res.objectSid] = 0

	for res in current_app.db.session.query(ADUser.objectSid)\
		.filter_by(ad_id = graphs[graphid].domain_id)\
		.filter(ADUser.UAC_DONT_REQUIRE_PREAUTH == True).all():
		
		target_sids[res[0]] = 0

	res = GraphData()
	for dst_sid in da_sids:
		for src_sid in target_sids:
			res += graphs[graphid].shortest_paths(src_sid, dst_sid)

	return res.to_dict(format = format)

def query_path_tohighvalue(graphid, format = 'vis'):
	if graphid not in graphs:
		load(graphid)

	target_sids = {}
	da_sids = {}

	for res in current_app.db.session.query(EdgeLookup.oid)\
		.filter_by(ad_id = graphs[graphid].domain_id)\
		.filter(EdgeLookup.oid == ADObjProps.oid)\
		.filter(ADObjProps.ad_id == graphs[graphid].domain_id)\
		.filter(ADObjProps.prop == 'HVT')\
		.all():
		
		target_sids[res[0]] = 0

	res = GraphData()
	for dst_sid in da_sids:
		for src_sid in target_sids:
			res += graphs[graphid].shortest_paths(dst=dst_sid)

	return res.to_dict(format = format)

def query_path_ownedda(graphid, format = 'vis'):
	if graphid not in graphs:
		load(graphid)

	target_sids = {}
	da_sids = {}

	for res in current_app.db.session.query(Group).filter_by(ad_id = graphs[graphid].domain_id).filter(Group.objectSid.like('%-512')).all():
		da_sids[res.objectSid] = 0

	for res in current_app.db.session.query(EdgeLookup.oid)\
		.filter_by(ad_id = graphs[graphid].domain_id)\
		.filter(EdgeLookup.oid == ADObjProps.oid)\
		.filter(ADObjProps.ad_id == graphs[graphid].domain_id)\
		.filter(ADObjProps.prop == 'OWNED')\
		.all():
		
		target_sids[res[0]] = 0

	res = GraphData()
	for dst_sid in da_sids:
		for src_sid in target_sids:
			res += graphs[graphid].shortest_paths(src_sid, dst_sid)

	return res.to_dict(format = format)

def query_path_fromowned(graphid, format = 'vis'):
	if graphid not in graphs:
		load(graphid)

	target_sids = {}

	for res in current_app.db.session.query(EdgeLookup.oid)\
		.filter_by(ad_id = graphs[graphid].domain_id)\
		.filter(EdgeLookup.oid == ADObjProps.oid)\
		.filter(ADObjProps.ad_id == graphs[graphid].domain_id)\
		.filter(ADObjProps.prop == 'OWNED')\
		.all():
		
		target_sids[res[0]] = 0

	res = GraphData()
	for src_sid in target_sids:
		res += graphs[graphid].shortest_paths(src=src_sid)

	return res.to_dict(format = format)


def list_nodes(graphid, with_data = False):
	if graphid not in graphs:
		return 'Graph Not Found', 404
	nodes = []
	for node in graphs[graphid].get_node():
		nodes.append(node.to_dict())
	return nodes

def get_node(graphid, nodeid):
	if graphid not in graphs:
		return 'Graph Not Found', 404
	return graphs[graphid].get_node(nodeid)

def query_path_all(graphid):
	if graphid not in graphs:
		return 'Graph Not Found', 404
	return graphs[graphid].show_all().to_dict(format = 'vis')

def search_sid(graphid, sid):
	return {}

def search_cn(graphid, cn):
	return {}

def stat_distance(graphid, sid):
	if graphid not in graphs:
		return 'Graph Not Found', 404
	distances = graphs[graphid].distances_from_node(sid)
	
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