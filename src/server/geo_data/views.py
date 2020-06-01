# src/server/auth/views.py
import json
import logging
from os import makedirs
from os.path import dirname, join, abspath, exists

from flask import Blueprint, request, make_response, jsonify, Response
from flask.views import MethodView
from sqlalchemy import func

from src.server import db
from src.server.models import TestPolygon, User, Crop
from src.server.errors import getError, invalid_token_error
from src.server.geo_data.utils import tile_ul, pathToTile, tileIsValid, tileToEnvelope, envelopeToBoundsSQL, envelopeToSQL

geo_blueprint = Blueprint('geo', __name__)

BASE_DIR = dirname(abspath(__file__))
CACHE_DIR = join(BASE_DIR,'cache')

CACHE_PATH="cache/"

TEST_TABLE = {
    'table':       'geodata',
    'srid':        '4326',
    'geomColumn':  'geom',
    'attrColumns': 'id, raster_val, ST_Area(ST_Transform(t.geom, 3857)) as area'
    }

TABLE = {
    'table':       'crops',
    'srid':        '2100',
    'geomColumn':  'geom',
    'attrColumns': 'shape_leng, shape_area, S1Pix, S2Pix, CT_decl, CT_pred, CT_conf, objectid'
    }

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
                polygons = db.session.query(TestPolygon.id, TestPolygon.raster_val, func.ST_AsGeoJSON(func.ST_Transform(TestPolygon.geom, 3857)), func.ST_Area(func.ST_Transform(TestPolygon.geom, 3857))).all()
                raster_vals = list(map(lambda t: t[0],db.session.query(func.distinct(TestPolygon.raster_val)).order_by(TestPolygon.raster_val).all()))
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

class GeoTestTileView(MethodView):

    def get(self, z, x, y):
        path = '/' + '/'.join(request.path.split('/')[2:])
        tile = pathToTile(path)
        if not (tile and tileIsValid(tile)):
            responseObject = {
                'success': False,
                'error': "invalid tile path: %s" % (path)
            }
            return make_response(jsonify(responseObject)), 400

        tilefolder = "{}/{}/{}".format(CACHE_DIR,z,x)
        tilepath = "{}/{}.pbf".format(tilefolder,y)

        if not exists(tilepath):
            env = tileToEnvelope(tile)
            sql = envelopeToSQL(env, TEST_TABLE)
            tile = db.engine.execute(sql).fetchone()[0]
            if not exists(tilefolder):
                makedirs(tilefolder)

            with open(tilepath, 'wb') as f:
                f.write(tile)
                f.close()
        else:
            tile = open(tilepath, 'rb').read()

        return Response(
            tile,
            mimetype="text/plain",
            headers={
                "Content-Type": "application/octet-stream",
                "Access-Control-Allow-Origin": "*"
            }
        )

class GeoTestFilters(MethodView):
    def post(self):
        auth_header = request.headers.get('Authorization')
        if auth_header:
            auth_token = auth_header
        else:
            auth_token = ''
        if auth_token:
            resp = User.decode_auth_token(auth_token)
            if not isinstance(resp, str):
                raster_vals = list(map(lambda t: t[0],db.session.query(func.distinct(TestPolygon.raster_val)).order_by(TestPolygon.raster_val).all()))
                responseObject = {
                    'success': True,
                    'filters': raster_vals
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

class CropsView(MethodView):

    def get(self, z, x, y):
        path = '/' + '/'.join(request.path.split('/')[2:])
        tile = pathToTile(path)
        if not (tile and tileIsValid(tile)):
            responseObject = {
                'success': False,
                'error': "invalid tile path: %s" % (path)
            }
            return make_response(jsonify(responseObject)), 400

        tilefolder = "{}/{}/{}".format(CACHE_DIR,z,x)
        tilepath = "{}/{}.pbf".format(tilefolder,y)

        if not exists(tilepath):
            env = tileToEnvelope(tile)
            sql = envelopeToSQL(env, TABLE)
            tile = db.engine.execute(sql).fetchone()[0]
            if not exists(tilefolder):
                makedirs(tilefolder)

            with open(tilepath, 'wb') as f:
                f.write(tile)
                f.close()
        else:
            tile = open(tilepath, 'rb').read()

        return Response(
            tile,
            mimetype="text/plain",
            headers={
                "Content-Type": "application/octet-stream",
                "Access-Control-Allow-Origin": "*"
            }
        )

class CropsFilters(MethodView):
    def post(self):
        auth_header = request.headers.get('Authorization')
        if auth_header:
            auth_token = auth_header
        else:
            auth_token = ''
        if auth_token:
            resp = User.decode_auth_token(auth_token)
            if not isinstance(resp, str):
                raster_vals = list(map(lambda t: t[0],db.session.query(func.distinct(TestPolygon.raster_val)).order_by(TestPolygon.raster_val).all()))
                responseObject = {
                    'success': True,
                    'filters': raster_vals
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
get_geojson_view = GeoJsonView.as_view('get_geojson_view')
get_test_tile_view = GeoTestTileView.as_view('get_test_tile_view')
get_test_filters = GeoTestFilters.as_view('get_test_filters')
get_crops_view = CropsView.as_view('get_crops_view')
get_crops_filters = CropsFilters.as_view('get_crops_filters')

# add Rules for API Endpoints
geo_blueprint.add_url_rule(
    '/geo/getcretandata',
    view_func=get_geojson_view,
    methods=['POST']
)

geo_blueprint.add_url_rule(
    '/testTiles/<int:z>/<int:x>/<int:y>.pbf',
    view_func=get_test_tile_view,
    methods=['GET']
)

geo_blueprint.add_url_rule(
    '/getTestFilters',
    view_func=get_test_filters,
    methods=['POST']
)

geo_blueprint.add_url_rule(
    '/crops/<int:z>/<int:x>/<int:y>.pbf',
    view_func=get_crops_view,
    methods=['GET']
)

geo_blueprint.add_url_rule(
    '/getCropsFilters',
    view_func=get_crops_filters,
    methods=['GET']
)

