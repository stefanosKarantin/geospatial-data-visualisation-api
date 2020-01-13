from sqlalchemy.orm import relationship
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
db = SQLAlchemy()

class Token(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(
        db.String(40), db.ForeignKey('client.client_id', ondelete='CASCADE'),
        nullable=False,
    )
    user_id = db.Column(
        db.Integer, db.ForeignKey('user.id', ondelete='CASCADE')
    )
    user = relationship('User')
    client = relationship('Client')
    token_type = db.Column(db.String(40))
    access_token = db.Column(db.String(255))
    refresh_token = db.Column(db.String(255))
    expires = db.Column(db.DateTime)
    scope = db.Column(db.Text)

    def __init__(self, **kwargs):
        expires_in = kwargs.pop('expires_in', None)
        if expires_in is not None:
            self.expires = datetime.utcnow() + timedelta(seconds=expires_in)

        for k, v in kwargs.items():
            setattr(self, k, v)

    @property
    def scopes(self):
        if self.scope:
            return self.scope.split()
        return []

    def delete(self):
        db.session.delete(self)
        db.session.commit()
        return self
