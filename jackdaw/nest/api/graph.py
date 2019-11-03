# System modules
from datetime import datetime
from jackdaw.nest.graph.domain import DomainGraph

# 3rd party modules
from flask import make_response, abort, current_app

db_conn = 'sqlite:////home/devel/Desktop/test22.db'
graph_id_ctr = 1
graphs = {}

def create(adid):
    global graph_id_ctr
    dg = DomainGraph(db_conn)
    dg.construct(adid)
    graphs[graph_id_ctr] = dg
    graph_id_ctr += 1
    return {'graphid' : graph_id_ctr - 1}

def delete(graphid):
    return {}

def get(graphid):
    return {}

def query_path(graphid, src, dst):
    return {}

def search_sid(graphid, sid):
    return {}

def search_cn(graphid, cn):
    return {}