# src/server/auth/views.py
import ast
import base64
import json
from os import makedirs
from os.path import dirname, join, abspath, exists

import psycopg2
from flask import Blueprint, request, make_response, jsonify
from flask.views import MethodView
from mercantile import bounds
from sqlalchemy import func, text
from sqlalchemy.sql import select, column, functions
from sqlalchemy.dialects.postgresql import BYTEA
from geoalchemy2 import Geometry
from geoalchemy2.functions import GenericFunction

from src.server import db
from src.server.models import Polygon, User
from src.server.errors import getError, invalid_token_error
from src.server.geo_data.utils import tile_ul

geo_blueprint = Blueprint('geo', __name__)

BASE_DIR = dirname(abspath(__file__))
CACHE_DIR = join(BASE_DIR,'cache')

class ST_AsMVTGeom(GenericFunction):
    name = 'ST_AsMVTGeom'
    type = Geometry


class ST_AsMVT(functions.GenericFunction):
    type = BYTEA

class GeoJsonView(MethodView):
    def post(self):
        auth_header = request.headers.get('Authorization')
        if auth_header:
            auth_token = auth_header
        else:
            auth_token = ''
        if auth_token:
            resp = User.decode_auth_token(auth_token)
            if not isinstance(resp, str):
                polygons = db.session.query(Polygon.id, Polygon.raster_val, func.ST_AsGeoJSON(func.ST_Transform(Polygon.geom, 3857)), func.ST_Area(func.ST_Transform(Polygon.geom, 3857))).limit(5000).all()
                raster_vals = list(map(lambda t: t[0],db.session.query(func.distinct(Polygon.raster_val)).order_by(Polygon.raster_val).all()))
                responseObject = {
                    'success': True,
                    'polygons': polygons,
                    'rasterValues': raster_vals
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

class GeoTileView(MethodView):
    def get(self, z=0, x=0, y=0):

        bbox = bounds(x,y,z)
        print(x,y,z)
        tile = None

        tilefolder = "{}/{}/{}".format(CACHE_DIR,z,x)
        tilepath = "{}/{}.pbf".format(tilefolder,y)

        if not exists(tilepath):
            # query = text("SELECT ST_AsMVT(tile, 'layer', 4096, 'geom') FROM (" \
            # "SELECT id, raster_val, ST_AsMVTGeom(geom, ST_MakeEnvelope(" \
            #     "{}, {} ,{}, {}, 4326" \
            # "), 4096, 0, false) AS geom FROM geodata) AS tile".format(bbox[0], bbox[1], bbox[2], bbox[3]))

            # tile = db.engine.execute(query).fetchone()[0]

            subq = select([
                func.ST_AsMVTGeom(func.ST_Transform(Polygon.geom, 3857),
                    func.ST_MakeEnvelope(
                        bbox[0], bbox[1], bbox[2], bbox[3], 3857
                    ),
                    4096,
                    256,
                    False
                ).label('geom')
            ])
            subq = subq.alias('q')

            q = select([func.ST_AsMVT(column('q'), 'layer', 4096, 'geom')]).select_from(subq).alias('mvtgeom')

            conn = db.engine.connect()

            tile = conn.scalar(q)

            # tile = db.session.query(q).one()[0]
            # print(tile)
            # print(tile.st_asmvt)
            if not exists(tilefolder):
                makedirs(tilefolder)

            with open(tilepath, 'wb') as f:
                f.write(tile)
                f.close()
                conn.close()
        else:
            tile = open(tilepath, 'rb').read()

        response = make_response(tile)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Content-Type'] = "application/octet-stream"
        return response, 200

# define the API resources
get_geojson_view = GeoJsonView.as_view('get_geojson_view')
get_tile_view = GeoTileView.as_view('get_tile_view')

# add Rules for API Endpoints
geo_blueprint.add_url_rule(
    '/geo/getcretandata',
    view_func=get_geojson_view,
    methods=['POST']
)

geo_blueprint.add_url_rule(
    '/tiles/<int:z>/<int:x>/<int:y>',
    view_func=get_tile_view,
    methods=['GET']
)
