# src/server/auth/views.py


from flask import Blueprint, request, make_response, jsonify
from flask.views import MethodView

from src.server import bcrypt, db
from src.server.models import User, BlacklistToken
from src.server.errors import *

auth_blueprint = Blueprint('auth', __name__)

class RegisterAPI(MethodView):
    """
    User Registration Resource
    """

    def post(self):
        # get the post data
        post_data = request.get_json()
        # check if user already exists
        user = User.query.filter_by(email=post_data.get('email')).first()
        if not user:
            try:
                user = User(
                    email=post_data.get('email'),
                    password=post_data.get('password')
                )
                # insert the user
                db.session.add(user)
                db.session.commit()
                # generate the auth token
                auth_token = user.encode_auth_token(user.id)
                auth_refresh_token = user.encode_auth_refresh_token(user.id)
                responseObject = {
                    'success': True,
                    'message': 'Successfully registered.',
                    'email': user.email,
                    'auth_token': auth_token.decode(),
                    'auth_refresh_token': auth_refresh_token.decode()
                }
                return make_response(jsonify(responseObject)), 201
            except Exception as e:
                responseObject = {
                    'success': False,
                    **getError(server_error)
                }
                return make_response(jsonify(responseObject)), 500
        else:
            responseObject = {
                'success': False,
                **getError(user_exist_error)
            }
            return make_response(jsonify(responseObject)), 202


class LoginAPI(MethodView):
    """
    User Login Resource
    """
    def post(self):
        # get the post data
        post_data = request.get_json()
        try:
            # fetch the user data
            user = User.query.filter_by(
                email=post_data.get('email')
            ).first()
            if user and bcrypt.check_password_hash(
                user.password, post_data.get('password')
            ):
                auth_token = user.encode_auth_token(user.id)
                auth_refresh_token = user.encode_auth_refresh_token(user.id)
                if auth_token and auth_refresh_token:
                    responseObject = {
                        'success': True,
                        'message': 'Successfully logged in.',
                        'email': user.email,
                        'auth_token': auth_token.decode(),
                        'auth_refresh_token': auth_refresh_token.decode()
                    }
                    return make_response(jsonify(responseObject)), 200
            else:
                responseObject = {
                    'success': False,
                    **getError(credentials_error)
                }
                return make_response(jsonify(responseObject)), 202
        except Exception as e:
            responseObject = {
                'success': False,
                **getError(server_error)

            }
            return make_response(jsonify(responseObject)), 500


class UserAPI(MethodView):
    """
    User Resource
    """
    def get(self):
        # get the auth token
        auth_header = request.headers.get('Authorization')
        if auth_header:
            auth_token = auth_header
        else:
            auth_token = ''
        if auth_token:
            resp = User.decode_auth_token(auth_token)
            if not isinstance(resp, str):
                user = User.query.filter_by(id=resp).first()
                responseObject = {
                    'success': True,
                    'data': {
                        'user_id': user.id,
                        'email': user.email,
                        'admin': user.admin,
                        'registered_on': user.registered_on
                    }
                }
                return make_response(jsonify(responseObject)), 200
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


class LogoutAPI(MethodView):
    """
    Logout Resource
    """
    def post(self):
        # get auth token
        auth_header = request.headers.get('Authorization')
        if auth_header:
            auth_token = auth_header
        else:
            auth_token = ''
        if auth_token:
            resp = User.decode_auth_token(auth_token)
            if not isinstance(resp, str):
                # mark the token as blacklisted
                blacklist_token = BlacklistToken(token=auth_token)
                try:
                    # insert the token
                    db.session.add(blacklist_token)
                    db.session.commit()
                    responseObject = {
                        'success': True,
                        'message': 'Successfully logged out.'
                    }
                    return make_response(jsonify(responseObject)), 200
                except Exception as e:
                    responseObject = {
                        'success': False,
                        'message': e
                    }
                    return make_response(jsonify(responseObject)), 500
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

class RefreshTokenAPI(MethodView):
    """
    Refresh Token Resource
    """
    def post(self):
        # get auth token
        post_data = request.get_json()
        auth_header = request.headers.get('Authorization')
        if auth_header:
            auth_refresh_token = auth_header
        else:
            auth_refresh_token = ''
        user = User.query.filter_by(
            email=post_data.get('email')
        ).first()
        if user:
            if auth_refresh_token:
                resp = User.decode_auth_refresh_token(auth_refresh_token)
                if not isinstance(resp, str):
                    # mark the token as blacklisted
                    blacklist_token = BlacklistToken(token=auth_refresh_token)
                    try:
                        # insert the token
                        db.session.add(blacklist_token)
                        db.session.commit()
                        auth_token = user.encode_auth_token(user.id)
                        new_auth_refresh_token = user.encode_auth_refresh_token(user.id)
                        if auth_token and new_auth_refresh_token:
                            responseObject = {
                                'success': True,
                                'message': 'Successfully refreshed token.',
                                'auth_token': auth_token.decode(),
                                'auth_refresh_token': new_auth_refresh_token.decode()
                            }
                            return make_response(jsonify(responseObject)), 200
                    except Exception as e:
                        responseObject = {
                            'success': False,
                            'message': e
                        }
                        return make_response(jsonify(responseObject)), 500
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
        else:
                responseObject = {
                    'success': False,
                     **getError(user_doesnt_exist_error)
                }
                return make_response(jsonify(responseObject)), 202

# define the API resources
registration_view = RegisterAPI.as_view('register_api')
login_view = LoginAPI.as_view('login_api')
user_view = UserAPI.as_view('user_api')
logout_view = LogoutAPI.as_view('logout_api')
refresh_token_view = RefreshTokenAPI.as_view('refresh_token_api')

# add Rules for API Endpoints
auth_blueprint.add_url_rule(
    '/auth/register',
    view_func=registration_view,
    methods=['POST']
)
auth_blueprint.add_url_rule(
    '/auth/login',
    view_func=login_view,
    methods=['POST']
)
auth_blueprint.add_url_rule(
    '/auth/status',
    view_func=user_view,
    methods=['GET']
)
auth_blueprint.add_url_rule(
    '/auth/logout',
    view_func=logout_view,
    methods=['POST']
)
auth_blueprint.add_url_rule(
    '/auth/refresh',
    view_func=refresh_token_view,
    methods=['POST']
)
