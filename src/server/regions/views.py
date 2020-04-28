# src/server/regions/views.py
import json
import logging
from os.path import dirname, join, abspath

from flask import Blueprint, request, make_response, jsonify
from flask.views import MethodView

from src.server.models import User
from src.server.errors import getError, invalid_token_error
from src.server.regions.models import Region_db

regions_blueprint = Blueprint('regions', __name__)

BASE_DIR = dirname(abspath(__file__))
CACHE_DIR = join(BASE_DIR,'cache')

CACHE_PATH="cache/"

class Regions(MethodView):
    def post(self):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            responseObject = {
                'success': False,
                **getError(invalid_token_error)
            }
            return make_response(jsonify(responseObject)), 401

        auth_token = auth_header
        resp = User.decode_auth_token(auth_token)
        if not isinstance(resp, str):
            regions = Region_db.getRegions()
            responseObject = {
                'success': True,
                'regions': regions
            }
            print(jsonify(responseObject), flush=True)
            return make_response(json.dumps(responseObject)), 200
        else:
            responseObject = {
                'success': False,
                'message': resp
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
