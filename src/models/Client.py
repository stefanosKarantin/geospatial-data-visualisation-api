from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Client(db.Model):
    # id = db.Column(db.Integer, primary_key=True)
    # human readable name
    name = db.Column(db.String(40))
    client_id = db.Column(db.String(40), primary_key=True)
    client_secret = db.Column(db.String(55), unique=True, index=True,
                              nullable=False)
    client_type = db.Column(db.String(20), default='public')
    _redirect_uris = db.Column(db.Text)
    default_scope = db.Column(db.Text, default='email address')

    @property
    def user(self):
        return User.query.get(1)

    @property
    def redirect_uris(self):
        if self._redirect_uris:
            return self._redirect_uris.split()
        return []

    @property
    def default_redirect_uri(self):
        return self.redirect_uris[0]

    @property
    def default_scopes(self):
        if self.default_scope:
            return self.default_scope.split()
        return []

    @property
    def allowed_grant_types(self):
        return ['authorization_code', 'password', 'client_credentials',
                'refresh_token']
