

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import make_transient
from tqdm import tqdm
from sqlalchemy import func


def shortest_path(con, graphname, src = None, dst = None):
	if src is not None and dst is not None:
		qry_template = "SET graph_path = %s; match p = allshortestpaths( (l1:node)-[:edge*]->(l2:node) ) where l1.sid = '%s' and l2.sid = '%s' return nodes(p);"
		qry = qry_template % (graphname, src, dst)
	elif src is not None and dst is None:
		qry_template = "SET graph_path = %s; match p = allshortestpaths( (l1:node)-[:edge*]->(l2:node) ) where l1.sid = '%s' return nodes(p);"
		qry = qry_template % (graphname, src, dst)
	elif src is None and dst is not None:
		qry_template = "SET graph_path = %s; match p = allshortestpaths( (l1:node)-[:edge*]->(l2:node) ) where l2.sid = '%s' return nodes(p);"
		qry = qry_template % (graphname, src, dst)
	elif src is None and dst is None:
		raise Exception('At least src or dst must be supplied!')
	rs = con.execute(qry)

	for row in rs:
		print(row)


def main():
	import argparse
	parser = argparse.ArgumentParser(description='Gather gather gather')
	parser.add_argument('-v', '--verbose', action='count', default=0, help='Increase verbosity, can be stacked')
	parser.add_argument('--sql',  help='SQL connection string.')
	
	subparsers = parser.add_subparsers(help = 'migration type')
	subparsers.required = True
	subparsers.dest = 'command'

	raw_group = subparsers.add_parser('raw', help='Full migration')
	raw_group.add_argument('query',  help='query')

	args = parser.parse_args()

	eng = create_engine(args.sql)
	con = eng.connect()

	graphname = 'graph1'
	src = 'S-1-5-21-796845957-1547161642-839522115-2779'
	dst = 'S-1-5-21-796845957-1547161642-839522115-512'
	shortest_path(con, graphname, src, dst)
	


if __name__ == '__main__':
	main()
	
	
	