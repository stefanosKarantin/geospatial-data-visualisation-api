# src/server/__init__.py

import os

from flask import Flask
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

app_settings = os.getenv(
    'APP_SETTINGS',
    'src.server.config.DevelopmentConfig'
)
app.config.from_object(app_settings)

bcrypt = Bcrypt(app)
db = SQLAlchemy(app)

from src.server.auth.views import auth_blueprint
from src.server.geo_data.views import geo_blueprint
from src.server.regions.views import regions_blueprint

app.register_blueprint(auth_blueprint)
app.register_blueprint(geo_blueprint)
app.register_blueprint(regions_blueprint)