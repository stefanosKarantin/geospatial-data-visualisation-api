from sqlalchemy.orm import relationship
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Grant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('user.id', ondelete='CASCADE')
    )
    user = relationship('User')

    client_id = db.Column(
        db.String(40), db.ForeignKey('client.client_id', ondelete='CASCADE'),
        nullable=False,
    )
    client = relationship('Client')
    code = db.Column(db.String(255), index=True, nullable=False)

    redirect_uri = db.Column(db.String(255))
    scope = db.Column(db.Text)
    expires = db.Column(db.DateTime)

    def delete(self):
        db.session.delete(self)
        db.session.commit()
        return self

    @property
    def scopes(self):
        if self.scope:
            return self.scope.split()
        return None