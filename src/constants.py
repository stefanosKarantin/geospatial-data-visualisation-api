""" Constants file for Auth0's seed project
"""

from os import environ
AUTH0_CLIENT_ID = '206578547470-qtpfqnnaik8uci4gc415tj1428pan031.apps.googleusercontent.com'
AUTH0_CLIENT_SECRET = 'G8zff-zx4YlwqJ-29UNO3TUB'
AUTH0_CALLBACK_URL = 'http://localhost/authenticate/callback'
AUTH0_DOMAIN = 'http://localhost'
AUTH0_AUDIENCE = 'AUTH0_AUDIENCE'
PROFILE_KEY = 'profile'
SECRET_KEY = 'ThisIsTheSecretKey'
JWT_PAYLOAD = 'jwt_payload'

GOOGLE_CLIENT_ID = environ.get("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = environ.get("GOOGLE_CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)