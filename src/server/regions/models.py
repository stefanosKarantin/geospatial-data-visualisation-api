from geoalchemy2 import Geometry
from sqlalchemy import func

from src.server import db
class Region_db(db.Model):
    """
    Model of regions multipoligons
    """
    __tablename__ = 'regions'

    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String)
    geom = db.Column(Geometry('MULTIPOLYGON'))

    @classmethod
    def getRegions(cls):
        return db.session.query(
            cls.id,
            cls.name,
            func.ST_AsGeoJSON(
                func.ST_Transform(cls.geom, 3857)
            ), 
            func.ST_Area(
                func.ST_Transform(cls.geom, 3857)
            )
        ).all()
