# src/server/auth/views.py
import ast
import base64
import io
import json
import logging
from os import makedirs
from os.path import dirname, join, abspath, exists
import re

import psycopg2
from flask import Blueprint, request, make_response, jsonify, Response
from flask.views import MethodView
from mercantile import bounds
from sqlalchemy import func, text
from sqlalchemy.sql import select, column, functions
from sqlalchemy.dialects.postgresql import BYTEA
from geoalchemy2 import Geometry
from geoalchemy2.functions import GenericFunction

from src.server import db
from src.server.models import Region, User
from src.server.errors import getError, invalid_token_error
from src.server.geo_data.utils import tile_ul

regions_blueprint = Blueprint('regions', __name__)

BASE_DIR = dirname(abspath(__file__))
CACHE_DIR = join(BASE_DIR,'cache')

CACHE_PATH="cache/"

class Regions(MethodView):
    def post(self):
        auth_header = request.headers.get('Authorization')
        if auth_header:
            auth_token = auth_header
        else:
            auth_token = ''
        if auth_token:
            resp = User.decode_auth_token(auth_token)
            if not isinstance(resp, str):
                regions = db.session.query(Region.id, Region.name, func.ST_AsGeoJSON(func.ST_Transform(Region.geom, 3857)), func.ST_Area(func.ST_Transform(Region.geom, 3857))).all()
                responseObject = {
                    'success': True,
                    'regions': regions
                }

                return make_response(jsonify(responseObject)), 200
            else:
                responseObject = {
                    'success': False,
                    'message': resp
                }
                return make_response(jsonify(responseObject)), 401
        else:
            responseObject = {
                'success': False,
                **getError(invalid_token_error)
            }
            return make_response(jsonify(responseObject)), 401


# define the API resources
regions_view = Regions.as_view('regions_view')

# add Rules for API Endpoints
regions_blueprint.add_url_rule(
    '/geo/regions',
    view_func=regions_view,
    methods=['POST']
)
