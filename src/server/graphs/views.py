# src/server/regions/views.py
import json
import logging
from os.path import dirname, join, abspath
from functools import reduce
import pandas as pd

from flask import Blueprint, request, make_response, jsonify
from flask.views import MethodView

from src.server.models import User, Crop
from src.server.errors import getError, invalid_token_error

graphs_blueprint = Blueprint('graphs', __name__)

class Graphs(MethodView):
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
            cropsMetadata = Crop.getCropsMetadata()
            graphs = self.getGraphs(cropsMetadata)

            responseObject = {
                'success': True,
                'graphs': graphs
            }
            print(jsonify(responseObject), flush=True)
            return make_response(json.dumps(responseObject)), 200
        else:
            responseObject = {
                'success': False,
                'message': resp
            }
            return make_response(jsonify(responseObject)), 401        

    @staticmethod
    def getConfData(data):
        i = pd.Index([1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,19,20,21], name='ct_decl')
        
        actual = pd.DataFrame(data.groupby('ct_decl')['ct_decl'].sum())
        actual.columns = ['actual']

        pred_true = pd.DataFrame(data.groupby('ct_decl').apply(lambda g: (g.ct_decl == g.ct_pred).sum()))
        pred_true.columns = ['pred_true']
        
        pred_false = pd.DataFrame(data.groupby('ct_pred').apply(lambda g: (g.ct_decl != g.ct_pred).sum()))
        pred_false.columns = ['pred_false']
        
        confusion = pd.DataFrame(index=i).join(actual, on='ct_decl')
        confusion = confusion.join(pred_true, on='ct_decl')
        confusion = confusion.join(pred_false, on=['ct_decl'])

        return confusion

    @classmethod
    def getGraphs(cls, cropsMetadata):
        data = pd.DataFrame(cropsMetadata, columns=['id', 'shape_leng', 'shape_area', 'ct_decl', 'ct_pred', 'region_id'])
        data = data[data['region_id'].notna()]
        regions = data.groupby('region_id')

        grouped_regions = [regions.get_group(x) for x in regions.groups]

        spatial_graph = {"{}".format(region['region_id'].unique()[0]): region.groupby('ct_decl')['shape_leng', 'shape_area'].mean().round(1).values.tolist() for region in grouped_regions}
        spatial_graph['total'] = data.groupby('ct_decl')['shape_leng', 'shape_area'].mean().round(1).values.tolist()

        confusion_graph = {"{}".format(region['region_id'].unique()[0]): cls.getConfData(region).fillna(0).astype(int).values.tolist() for region in grouped_regions}
        confusion_graph['total'] = cls.getConfData(data).fillna(0).astype(int).values.tolist()

        return {'spatial': spatial_graph, 'confusion': confusion_graph}


# define the API resources
graphs_view = Graphs.as_view('graphs_view')

# add Rules for API Endpoints
graphs_blueprint.add_url_rule(
    '/geo/graphs',
    view_func=graphs_view,
    methods=['POST']
)
