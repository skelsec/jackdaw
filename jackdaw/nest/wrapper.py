import os
import connexion
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
	def __init__(self, db_conn, bind_ip = '127.0.0.1', bind_port = 5000, debug = True, basedir = None, swagger_config = "swagger.yaml"):
		self.basedir = basedir
		self.db_conn_string = db_conn #connection string
		self.swagger_config = swagger_config
		self.bind_ip = bind_ip
		self.bind_port = bind_port
		self.debug = debug

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

		app.config['SQLALCHEMY_ECHO'] = False 
		app.config['SQLALCHEMY_DATABASE_URI'] = self.db_conn_string
		app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
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


