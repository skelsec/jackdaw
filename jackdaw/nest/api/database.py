
from flask_sqlalchemy import SQLAlchemy
from jackdaw.dbmodel.adinfo import JackDawADInfo
from flask import current_app
from jackdaw.dbmodel.pagination import paginate
import connexion
import datetime
import os
import zipfile
import glob
from jackdaw.dbmodel import get_session
from jackdaw.dbmodel.migrate import migrate

def upload(dbfile):
	file_to_upload = connexion.request.files['dbfile']
	uploads_folder = current_app.config['JACKDAW_WORK_DIR'].joinpath('uploads')
	uploads_folder.mkdir(parents=True, exist_ok=True)

	current_folder_base = 'upload_%s_%s' % (os.urandom(4).hex(), datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S"))
	current_folder = uploads_folder.joinpath(current_folder_base)

	current_folder.mkdir(parents=True, exist_ok=False)
	current_decompression_folder = current_folder.joinpath('decomp')
	current_decompression_folder.mkdir(parents=True, exist_ok=False)

	compressed_file_path = current_folder.joinpath('upload.zip')
	with open(str(compressed_file_path), "bw") as f:
		chunk_size = 4096
		while True:
			chunk = file_to_upload.stream.read(chunk_size)
			if len(chunk) == 0:
				break
			f.write(chunk)

	with zipfile.ZipFile(str(compressed_file_path), 'r') as zip_ref:
		zip_ref.extractall(str(current_decompression_folder))
	
	dbfile = None
	for filename in glob.glob(str(current_decompression_folder.joinpath('*.db'))):
		dbfile = filename
		break

	if dbfile is None:
		raise Exception('Could not find database file in zip!')

	sql_url = 'sqlite:///%s' % str(current_decompression_folder.joinpath(dbfile))
	print(sql_url)

	old_session = get_session(sql_url)
	migrate(old_session, current_app.db.session)

	return
