# System modules
from datetime import datetime
from jackdaw.nest.graph.domain import DomainGraph

# 3rd party modules
from flask import make_response, abort, current_app
from flask_sqlalchemy import SQLAlchemy


graph_id_ctr = 1
graphs = {}

def create(adid):
    global graph_id_ctr
    db = SQLAlchemy()
    dg = DomainGraph(dbsession = db.session)
    dg.construct(adid)
    graphs[graph_id_ctr] = dg
    graph_id_ctr += 1
    return {'graphid' : graph_id_ctr - 1}

def delete(graphid):
    return {}

def get(graphid):
    if graphid not in graphs:
        return {}
    res = graphs[graphid].all_shortest_paths()
    return res.to_dict()

def query_path(graphid, src = None, dst = None):
    if graphid not in graphs:
        return {}
    if src is None and dst is None:
        return {}
    res =  graphs[graphid].all_shortest_paths(src, dst)
    return res.to_dict(format = 'd3')

def list_nodes(graphid, with_data = False):
    if graphid not in graphs:
        return {}
    return graphs[graphid].get_node()

def get_node(graphid, nodeid):
    if graphid not in graphs:
        return {}
    return graphs[graphid].get_node(nodeid)

def query_path_all(graphid):
    if graphid not in graphs:
        return {}
    return graphs[graphid].show_all().to_dict(format = 'd3')

def search_sid(graphid, sid):
    return {}

def search_cn(graphid, cn):
    return {}