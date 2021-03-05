import os
import connexion
import pathlib
#ORDER IS IMPORTANT!!
from flask_sqlalchemy import SQLAlchemy
#from flask_marshmallow import Marshmallow

from jackdaw.nest.utils.encoder import UniversalFlaskEncoder

import connexion
import flask
from connexion.apps.flask_app import FlaskJSONEncoder

class ConfigurableFlaskApp(connexion.FlaskApp):
	def __init__(self, import_name, **kwargs):
		self.flask_args = _get_flask_args(kwargs)
		connexion_args = _get_connexion_args(kwargs)
		super().__init__(import_name, **connexion_args)

	def create_app(self):
		app = flask.Flask(self.import_name, **self.flask_args)
		app.json_encoder = FlaskJSONEncoder
		return app

def _get_flask_args(kwargs):
	return {k.replace('flask_', ''): v for k, v in kwargs.items() if k.startswith('flask_')}

def _get_connexion_args(kwargs):
	return {k: v for k, v in kwargs.items() if not k.startswith('flask_')}

class NestServer:
	def __init__(self, db_conn, bind_ip = '127.0.0.1', bind_port = 5000, debug = True, basedir = None, swagger_config = "swagger.yaml", graph_backend = 'graphtools', work_dir = './workdir'):
		self.basedir = basedir
		self.db_conn_string = db_conn #connection string
		self.swagger_config = swagger_config
		self.bind_ip = bind_ip
		self.bind_port = bind_port
		self.debug = debug
		self.work_dir = pathlib.Path(work_dir)
		self.graph_backend = graph_backend
		self.connex_app = None

	def setup(self):
		if self.basedir is None:
			self.basedir = os.path.abspath(os.path.dirname(__file__))

		#print(self.basedir)
		#print(self.db_conn_string)

		# Create the connexion application instance
		self.connex_app = ConfigurableFlaskApp(__name__, flask_instance_path =self.basedir, specification_dir='api')
		# Read the swagger.yml file to configure the endpoints
		self.connex_app.add_api(self.swagger_config)

		# Get the underlying Flask app instance
		app = self.connex_app.app
		#set custom JSON encoder
		app.json_encoder = UniversalFlaskEncoder

		if self.graph_backend.upper() == 'networkx'.upper():
			from jackdaw.nest.graph.backends.networkx.domaingraph import JackDawDomainGraphNetworkx
			graph_type = JackDawDomainGraphNetworkx
		elif self.graph_backend.upper() == 'igraph'.upper():
			from jackdaw.nest.graph.backends.igraph.domaingraph import JackDawDomainGraphIGraph
			graph_type = JackDawDomainGraphIGraph
		elif self.graph_backend.upper() == 'graphtools'.upper():
			from jackdaw.nest.graph.backends.graphtools.domaingraph import JackDawDomainGraphGrapthTools
			graph_type = JackDawDomainGraphGrapthTools

		pathlib.Path(self.work_dir).mkdir(parents=True, exist_ok=True)
		pathlib.Path(self.work_dir).joinpath('graphcache').mkdir(parents=True, exist_ok=True)

		app.config['DEBUG'] = False 
		app.config['SQLALCHEMY_ECHO'] = False 
		app.config['SQLALCHEMY_DATABASE_URI'] = self.db_conn_string
		app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
		app.config['SQLALCHEMY_RECORD_QUERIES'] = False
		app.config['JACKDAW_WORK_DIR'] = self.work_dir
		app.config['JACKDAW_GRAPH_BACKEND'] = self.graph_backend
		app.config['JACKDAW_GRAPH_BACKEND_OBJ'] = graph_type
		app.config['JACKDAW_GRAPH_DICT'] = {}
		app.config['JACKDAW_GRAPH_DICT_LOADING'] = {}
		
		#
		## Create the SQLAlchemy db instance
		db = SQLAlchemy(app)

		with self.connex_app.app.app_context():
			self.connex_app.app.db = db

		#
		## Initialize Marshmallow
		#ma = Marshmallow(app)

	def run(self):
		self.setup()
		self.connex_app.run(host=self.bind_ip, port=self.bind_port, debug=self.debug)


