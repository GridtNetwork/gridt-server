from itsdangerous import (TimedJSONWebSignatureSerializer
                                  as Serializer, BadSignature, SignatureExpired)
from flask import current_app

from passlib.apps import custom_app_context as pwd_context
from db import db

from models.association_movement_users import association_movement_users


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(32), index = True)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(32))
    movements = db.relationship('Movement',
        secondary=association_movement_users)

    def __init__(self, username, password, role='user'):
        self.username = username
        self.hash_password(password)
        self.role = role

    @classmethod
    def find_by_name(cls, query_username):
        return cls.query.filter_by(username=query_username).one_or_none()

    def hash_password(self, password):
        self.password_hash = pwd_context.hash(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def generate_auth_token(self, expiration=600):
        s = Serializer(current_app.config["SECRET_KEY"])
        return s.dumps({'id': self.id})

    @classmethod
    def verify_auth_token(cls, token):
        s = Serializer(current_app.config["SECRET_KEY"])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None
        except BadSignature:
            return None

        user = cls.query.get(data['id'])

        if data['id'] == None:
            return None
        return user

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()
