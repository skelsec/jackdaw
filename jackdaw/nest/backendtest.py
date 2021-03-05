
from jackdaw.nest.graph.domain import DomainGraph
from jackdaw.nest.graph.graphdata import GraphData
from jackdaw.nest.graph.domaindiff import DomainDiff
from jackdaw.dbmodel.adgroup import Group
from jackdaw.dbmodel.edgelookup import EdgeLookup
from jackdaw.dbmodel.edge import Edge
from jackdaw.dbmodel.aduser import ADUser

from jackdaw.nest.graph.backends.graphtools.domaingraph import JackDawDomainGraphGrapthTools
from jackdaw.dbmodel import get_session

import pprint

sql = 'sqlite:////home/devel/Desktop/1.db'
ad_id = 1
graph_id = 1
work_dir = '/home/devel/Desktop/projects/jackdaw/graphs'

print(sql)
session = get_session(sql)

a = JackDawDomainGraphGrapthTools(session, graph_id, work_dir)
a.load()
print('Loaded!')


#src_sid = 'S-1-5-21-796845957-1547161642-839522115-1286'
dst_sid = 'S-1-5-21-796845957-1547161642-839522115-512'

da_sids = {}
#target_sids = {}
#
#for res in session.query(ADUser.objectSid)\
#		.filter_by(ad_id = ad_id)\
#		.filter(ADUser.servicePrincipalName != None).all():
#		
#		target_sids[res[0]] = 0
#

for res in session.query(Group).filter_by(ad_id = ad_id).filter(Group.objectSid.like('%-512')).all():
		da_sids[res.objectSid] = 0
	
if len(da_sids) == 0:
	raise Exception('No DA!')
	
res = GraphData()
for sid in da_sids:
	res += a.shortest_paths(None, sid)

#res = GraphData()
#for src_sid in target_sids:
#	res += a.shortest_paths(src_sid, dst_sid)
#	#print(pprint.pprint(res.to_dict()))
#	print('src: %s dst: %s' % (src_sid, dst_sid))
#	
#	input()