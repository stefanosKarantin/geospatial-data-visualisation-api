# src/server/models.py


import jwt
import datetime

from geoalchemy2 import Geometry
from src.server import app, db, bcrypt#, api

def getTokenError(msg):
    return {
        'error': 'TOKEN_ERROR',
        'message': msg
    }

# successResponse = api.model('Model', {
#     'name': fields.String,
#     'address': fields.String,
#     'date_updated': fields.DateTime(dt_format='rfc822'),
# })

class User(db.Model):
    """ User Model for storing user related details """
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    registered_on = db.Column(db.DateTime, nullable=False)
    admin = db.Column(db.Boolean, nullable=False, default=False)

    def __init__(self, email, password, admin=False):
        self.email = email
        self.password = bcrypt.generate_password_hash(
            password, app.config.get('BCRYPT_LOG_ROUNDS')
        ).decode()
        self.registered_on = datetime.datetime.now()
        self.admin = admin

    def encode_auth_token(self, user_id):
        """
        Generates the Auth Token
        :return: string
        """
        try:
            payload = {
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=0, seconds=10),
                'iat': datetime.datetime.utcnow(),
                'sub': user_id
            }
            return jwt.encode(
                payload,
                app.config.get('SECRET_KEY'),
                algorithm='HS256'
            )
        except Exception as e:
            return e

    def encode_auth_refresh_token(self, user_id):
        """
        Generates the Auth Token
        :return: string
        """
        try:
            payload = {
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=0, minutes=60),
                'iat': datetime.datetime.utcnow(),
                'sub': user_id
            }
            return jwt.encode(
                payload,
                app.config.get('SECRET_REFRESH_KEY'),
                algorithm='HS256'
            )
        except Exception as e:
            return e

    @staticmethod
    def decode_auth_token(auth_token):
        """
        Validates the auth token
        :param auth_token:
        :return: integer|string
        """
        try:
            payload = jwt.decode(auth_token, app.config.get('SECRET_KEY'))
            is_blacklisted_token = BlacklistToken.check_blacklist(auth_token)
            if is_blacklisted_token:
                return getTokenError('Token blacklisted. Please log in again.')
            else:
                return payload['sub']
        except jwt.ExpiredSignatureError:
            return getTokenError('Signature expired. Please log in again.')
        except jwt.InvalidTokenError:
            return getTokenError('Invalid token. Please log in again.')

    @staticmethod
    def decode_auth_refresh_token(auth_refresh_token):
        """
        Validates the auth token
        :param auth_refresh_token:
        :return: integer|string
        """
        try:
            payload = jwt.decode(auth_refresh_token, app.config.get('SECRET_REFRESH_KEY'))
            is_blacklisted_token = BlacklistToken.check_blacklist(auth_refresh_token)
            if is_blacklisted_token:
                return ('Token blacklisted. Please log in again.')
            else:
                return payload['sub']
        except jwt.ExpiredSignatureError:
            return getTokenError('Signature expired. Please log in again.')
        except jwt.InvalidTokenError:
            return getTokenError('Invalid token. Please log in again.')


class BlacklistToken(db.Model):
    """
    Token Model for storing JWT tokens
    """
    __tablename__ = 'blacklist_tokens'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    token = db.Column(db.String(500), unique=True, nullable=False)
    blacklisted_on = db.Column(db.DateTime, nullable=False)

    def __init__(self, token):
        self.token = token
        self.blacklisted_on = datetime.datetime.now()

    def __repr__(self):
        return '<id: token: {}'.format(self.token)

    @staticmethod
    def check_blacklist(auth_token):
        # check whether auth token has been blacklisted
        res = BlacklistToken.query.filter_by(token=str(auth_token)).first()
        if res:
            return True
        else:
            return False

class TestPolygon(db.Model):
    """
    Model of cretan raster data
    """
    __tablename__ = 'geodata'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    raster_val = db.Column(db.Integer)
    geom = db.Column(Geometry('POLYGON'))

class Crop(db.Model):
    """
    Model of cretan raster data
    """
    __tablename__ = 'crops'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    raster_val = db.Column(db.Integer)
    geom = db.Column(Geometry('POLYGON'))
    shape_leng = db.Column(db.Float)
    shape_area = db.Column(db.Float)
    S1Pix = db.Column(db.Integer)
    S2Pix = db.Column(db.Integer)
    CT_decl = db.Column(db.Integer)
    CT_pred = db.Column(db.Integer)
    CT_conf = db.Column(db.Float)
    objectid = db.Column(db.Integer)