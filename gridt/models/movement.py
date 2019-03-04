from db import db
from models.user import User

from models.association_movement_users import association_movement_users

class Movement(db.Model):
    __tablename__ = 'movements'
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(50), nullable=False)
    short_description = db.Column(db.String(100))
    description = db.Column(db.String(1000))
    users = db.relationship('User',
            secondary=association_movement_users)

    def __init__(self, name, short_description=None):
        self.name = name
        self.short_description = short_description

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()
