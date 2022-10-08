
from pathlib import Path

from jackdaw import logger
from jackdaw.dbmodel.graphinfo import GraphInfo, GraphInfoAD
from jackdaw.dbmodel.adinfo import ADInfo

# creates graph cache file
def create(graph_id, dbsession, work_dir, backend_object, db_url):
	if isinstance(work_dir, str):
		work_dir = Path(work_dir)
	
	sqlite_file = None
	if db_url.lower().startswith('sqlite') is True:
		sqlite_file = db_url.replace('sqlite:///', '')

	logger.error(sqlite_file)
	gi = dbsession.query(GraphInfo).get(graph_id)
	graphid = gi.id
	graph_cache_dir = work_dir.joinpath('graphcache')
	graph_dir = graph_cache_dir.joinpath(str(gi.id))
	try:
		graph_dir.mkdir(parents=True, exist_ok=False)
	except Exception as e:
		logger.warning('Graph cache dir with ID %s already exists, skipping! Err %s' % (str(gi.id), str(e)))
		return graphid
			
	backend_object.create(dbsession, str(gi.id), graph_dir, sqlite_file = sqlite_file)
	
	return graphid