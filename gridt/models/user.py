from sqlalchemy.ext.associationproxy import association_proxy
from flask import current_app

from itsdangerous import (
    TimedJSONWebSignatureSerializer as Serializer,
    BadSignature,
    SignatureExpired,
)
from passlib.apps import custom_app_context as pwd_context

from db import db


class User(db.Model):
    '''
    Intuitive representation of users in the database.

    :param str username: Username that the user has chosen.
    :param str password: Password that the user has chosen.
    Right now, to find the leaders of a user the following code snippet can be used: ::

        user = Users.find_by_id(1)
        user_leaders = list(
            map(lambda a: a.leader, user.follower_associations)
        )

    :attribute password_hash: Hashed version of the users's password.
    :attribute follower_associations: All associations to movements where the follower is this user. Useful for determining the leaders of a user.
    :attribute movements: List of all movements that the user is subscribed to.

    :todo: Make a user.leaders dictionary attribute that has movements as the keys and lists of leaders as the values.
    '''
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), index=True)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(32))

    follower_associations = db.relationship(
        'MovementUserAssociation', foreign_keys='MovementUserAssociation.follower_id'
    )
    movements = association_proxy('follower_associations', 'movement',
            creator=lambda movement: MovementUserAssociation(movement=movement))

    def __init__(self, username, password, role='user'):
        self.username = username
        self.hash_password(password)
        self.role = role

    def __repr__(self):
        return f'<User {self.username}>'

    @classmethod
    def find_by_name(cls, query_username):
        return cls.query.filter_by(username=query_username).one_or_none()

    @classmethod
    def find_by_id(cls, id):
        return cls.query.get(id)

    def hash_password(self, password):
        '''
        Hash password and set it as the password_hash.
        :param str password: Password that is to be hashed.
        '''
        self.password_hash = pwd_context.hash(password)

    def verify_password(self, password):
        '''
        Verify that this password matches with the hashed version in the database.
        :rtype bool:
        '''
        return pwd_context.verify(password, self.password_hash)

    def generate_auth_token(self):
        '''
        Create an auth token that will be used to authenticate using the JWT scheme.
        :returns: serialized dictionary that contains the user id.
        :rtype str:
        '''
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'id': self.id})

    @classmethod
    def verify_auth_token(cls, token):
        '''
        Verify that the auth token is valid and not expired.

        :param str token: Token that is to be verified
        :rtype bool:
        '''
        s = Serializer(current_app.config['SECRET_KEY'])
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
