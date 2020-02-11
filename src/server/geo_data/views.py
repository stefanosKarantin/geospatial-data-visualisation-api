# src/server/auth/views.py
import ast
import json

from flask import Blueprint, request, make_response, jsonify
from flask.views import MethodView
from sqlalchemy import func

from src.server import db
from src.server.models import Polygon

geo_blueprint = Blueprint('geo', __name__)

class GeoJsonView(MethodView):
    def post(self):
        auth_header = request.headers.get('Authorization')
        if auth_header:
            auth_token = auth_header
        else:
            auth_token = ''
        if auth_token:
            polygons = db.session.query(Polygon.id, Polygon.raster_val, func.ST_AsGeoJSON(Polygon.geom)).all()
            print(polygons)
            responseObject = {
                'success': True,
                'polygons': polygons # list(map(lambda p: json.loads(p[0]), polygons))
            }

            return make_response(jsonify(responseObject)), 200
        else:
            responseObject = {
                'success': False,
                'message': 'Provide a valid auth token.'
            }
            return make_response(jsonify(responseObject)), 401

# define the API resources
get_geojson_view = GeoJsonView.as_view('get_geojson_view')

# add Rules for API Endpoints
geo_blueprint.add_url_rule(
    '/geo/getcretandata',
    view_func=get_geojson_view,
    methods=['POST']
)

