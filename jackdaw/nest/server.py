import os
from flask import render_template
import connexion
#ORDER IS IMPORTANT!!
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow



# Create the application instance
connex_app = connexion.App(__name__, specification_dir='./api')

# Read the swagger.yaml file to configure the endpoints
#app.add_api('swagger.yaml', resolver=RestyResolver('api'))
connex_app.add_api('swagger.yaml')

## Get the underlying Flask app instance
#app = connex_app.app
#
## Configure the SQLAlchemy part of the app instance
#app.config['SQLALCHEMY_ECHO'] = True
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////' + os.path.join(basedir, 'people.db')
#app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#
## Create the SQLAlchemy db instance
#db = SQLAlchemy(app)
#
## Initialize Marshmallow
#ma = Marshmallow(app)


# If we're running in stand alone mode, run the application
if __name__ == '__main__':
    connex_app.run(host='0.0.0.0', port=5000, debug=True)
