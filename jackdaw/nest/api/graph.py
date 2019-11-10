# System modules
from datetime import datetime
from jackdaw.nest.graph.domain import DomainGraph, GraphData

# 3rd party modules
from flask import make_response, abort, current_app
from flask import current_app


graph_id_ctr = 1
graphs = {}

def create(adid):
    global graph_id_ctr
    db = current_app.db
    dg = DomainGraph(dbsession = db.session)
    dg.construct(adid)
    graphs[graph_id_ctr] = dg
    graph_id_ctr += 1
    return {'graphid' : graph_id_ctr - 1}

def delete(graphid):
    return {}

def get(graphid):
    if graphid not in graphs:
        return 'Graph Not Found', 404
    res = graphs[graphid].all_shortest_paths()
    return res.to_dict()

def query_path(graphid, src = None, dst = None, format = 'd3'):
    if graphid not in graphs:
        return 'Graph Not Found', 404
    if src is None and dst is None:
        return {}
    res =  graphs[graphid].all_shortest_paths(src, dst)
    return res.to_dict(format = format)

def query_path_da(graphid, format = 'vis'):
    if graphid not in graphs:
        return 'Graph Not Found', 404
    
    da_sids = {}
    #searching for domain admin SID
    for node in graphs[graphid].get_node():
        if node.id.endswith('-512'):
            da_sids[node.id] = 1
    
    #print(da_sids)
    if len(da_sids) == 0:
        return 'Graph Not Found', 404
    
    res = GraphData()
    for sid in da_sids:
        res += graphs[graphid].all_shortest_paths(None, sid)


    #print(res)
    return res.to_dict(format = format)


def list_nodes(graphid, with_data = False):
    if graphid not in graphs:
        return 'Graph Not Found', 404
    nodes = []
    for node in graphs[graphid].get_node():
        nodes.append(node.to_dict())
    print(nodes)
    return nodes

def get_node(graphid, nodeid):
    if graphid not in graphs:
        return 'Graph Not Found', 404
    return graphs[graphid].get_node(nodeid)

def query_path_all(graphid):
    if graphid not in graphs:
        return 'Graph Not Found', 404
    return graphs[graphid].show_all().to_dict(format = 'd3')

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
    print(graphids)
    original = graphids['src']
    new = graphids['dst']
    
    users_added = {}
    users_removed = {}

    machines_added = {}
    machines_removed = {}

    groups_added = {}
    groups_removed = {}

    for sid, attrs in graphs[new].graph.nodes(data=True):
        print(sid)
        if not graphs[original].graph.has_node(sid):
            print(attrs)
            if attrs.get('node_type') == 'user':
                users_added[sid] = 1
            elif attrs.get('node_type') == 'machine':
                machines_added[sid] = 1
            elif attrs.get('node_type') == 'group':
                groups_added[sid] = 1
    
    for sid, attrs in graphs[original].graph.nodes(data=True):
        if not graphs[new].graph.has_node(sid):
            print(attrs)
            if attrs.get('node_type') == 'user':
                users_removed[sid] = 1
            elif attrs.get('node_type') == 'machine':
                machines_removed[sid] = 1
            elif attrs.get('node_type') == 'group':
                groups_removed[sid] = 1

    print(users_added)
    print(users_removed)
    print(machines_added)
    print(machines_removed)
    print(groups_added)
    print(groups_removed)

    return {}