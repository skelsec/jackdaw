import os
import connexion
#ORDER IS IMPORTANT!!
from flask_sqlalchemy import SQLAlchemy
#from flask_marshmallow import Marshmallow

from jackdaw.nest.utils.encoder import UniversalFlaskEncoder

basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'api'))

# Create the connexion application instance
connex_app = connexion.App(__name__, specification_dir=basedir)
# Read the swagger.yml file to configure the endpoints
connex_app.add_api("swagger.yaml")

# Get the underlying Flask app instance
app = connex_app.app
#set custom JSON encoder
app.json_encoder = UniversalFlaskEncoder

app.config['SQLALCHEMY_ECHO'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////home/devel/Desktop/test_hist.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#
## Create the SQLAlchemy db instance
db = SQLAlchemy(app)

with connex_app.app.app_context():
    connex_app.app.db = db

#
## Initialize Marshmallow
#ma = Marshmallow(app)
