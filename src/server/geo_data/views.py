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
from src.server.models import Polygon, User
from src.server.errors import getError, invalid_token_error
from src.server.geo_data.utils import tile_ul

geo_blueprint = Blueprint('geo', __name__)

BASE_DIR = dirname(abspath(__file__))
CACHE_DIR = join(BASE_DIR,'cache')

CACHE_PATH="cache/"

TABLE = {
    'table':       'geodata',
    'srid':        '4326',
    'geomColumn':  'geom',
    'attrColumns': 'id, raster_val, ST_Area(ST_Transform(t.geom, 3857)) as area'
    }

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
                polygons = db.session.query(Polygon.id, Polygon.raster_val, func.ST_AsGeoJSON(func.ST_Transform(Polygon.geom, 3857)), func.ST_Area(func.ST_Transform(Polygon.geom, 3857))).all()
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
    def pathToTile(self, path):
        m = re.search(r'^\/(\d+)\/(\d+)\/(\d+)\.(\w+)', path)
        if (m):
            return {'zoom':   int(m.group(1)),
                    'x':      int(m.group(2)),
                    'y':      int(m.group(3)),
                    'format': m.group(4)}
        else:
            return None

    def tileIsValid(self, tile):
        if not ('x' in tile and 'y' in tile and 'zoom' in tile):
            return False
        if 'format' not in tile or tile['format'] not in ['pbf', 'mvt', 'png']:
            return False
        size = 2 ** tile['zoom'];
        if tile['x'] >= size or tile['y'] >= size:
            return False
        if tile['x'] < 0 or tile['y'] < 0:
            return False
        return True

    def tileToEnvelope(self, tile):
        # Width of world in EPSG:3857
        worldMercMax = 20037508.3427892
        worldMercMin = -1 * worldMercMax
        worldMercSize = worldMercMax - worldMercMin
        # Width in tiles
        worldTileSize = 2 ** tile['zoom']
        # Tile width in EPSG:3857
        tileMercSize = worldMercSize / worldTileSize
        # Calculate geographic bounds from tile coordinates
        # XYZ tile coordinates are in "image space" so origin is
        # top-left, not bottom right
        env = dict()
        env['xmin'] = worldMercMin + tileMercSize * tile['x']
        env['xmax'] = worldMercMin + tileMercSize * (tile['x'] + 1)
        env['ymin'] = worldMercMax - tileMercSize * (tile['y'] + 1)
        env['ymax'] = worldMercMax - tileMercSize * (tile['y'])
        return env


    # Generate SQL to materialize a query envelope in EPSG:3857.
    # Densify the edges a little so the envelope can be
    # safely converted to other coordinate systems.
    def envelopeToBoundsSQL(self, env):
        DENSIFY_FACTOR = 4
        env['segSize'] = (env['xmax'] - env['xmin'])/DENSIFY_FACTOR
        sql_tmpl = 'ST_Segmentize(ST_MakeEnvelope({xmin}, {ymin}, {xmax}, {ymax}, 3857),{segSize})'
        return sql_tmpl.format(**env)


    # Generate a SQL query to pull a tile worth of MVT data
    # from the table of interest.
    def envelopeToSQL(self, env):
        tbl = TABLE.copy()
        tbl['env'] = self.envelopeToBoundsSQL(env)
        # Materialize the bounds
        # Select the relevant geometry and clip to MVT bounds
        # Convert to MVT format
        sql_tmpl = """
            WITH
            bounds AS (
                SELECT {env} AS geom,
                       {env}::box2d AS b2d
            ),
            mvtgeom AS (
                SELECT ST_AsMVTGeom(ST_Transform(t.{geomColumn}, 3857), bounds.b2d) AS geom,
                       {attrColumns}
                FROM {table} t, bounds
                WHERE ST_Intersects(t.{geomColumn}, ST_Transform(bounds.geom, {srid}))
            )
            SELECT ST_AsMVT(mvtgeom.*) FROM mvtgeom
        """
        return sql_tmpl.format(**tbl)

    def get(self, z, x, y):
        path = '/' + '/'.join(request.path.split('/')[2:])
        tile = self.pathToTile(path)
        if not (tile and self.tileIsValid(tile)):
            responseObject = {
                'success': False,
                'error': "invalid tile path: %s" % (path)
            }
            return make_response(jsonify(responseObject)), 400

        tilefolder = "{}/{}/{}".format(CACHE_DIR,z,x)
        tilepath = "{}/{}.pbf".format(tilefolder,y)

        if not exists(tilepath):
            env = self.tileToEnvelope(tile)
            sql = self.envelopeToSQL(env)
            tile = db.engine.execute(sql).fetchone()[0]
            if not exists(tilefolder):
                makedirs(tilefolder)

            with open(tilepath, 'wb') as f:
                f.write(tile)
                f.close()
        else:
            tile = open(tilepath, 'rb').read()
        # response = make_response(pbf)
        # response.headers['Access-Control-Allow-Origin'] = '*'
        # response.headers['Content-Type'] = "application/vnd.mapbox-vector-tile"
        return Response(
            tile,
            mimetype="text/plain",
            headers={
                "Content-Type": "application/octet-stream",
                "Access-Control-Allow-Origin": "*"
            }
        )

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
    '/tiles/<int:z>/<int:x>/<int:y>.pbf',
    view_func=get_tile_view,
    methods=['GET']
)
