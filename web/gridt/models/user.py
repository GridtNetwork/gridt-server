from sqlalchemy import not_
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm.collections import attribute_mapped_collection
from flask import current_app

from passlib.apps import custom_app_context as pwd_context
import hashlib

import datetime
import jwt

from gridt.db import db

from gridt.models.movement_user_association import MovementUserAssociation


class User(db.Model):
    """
    Intuitive representation of users in the database.

    :param str username: Username that the user has chosen.
    :param str email: Email that the user has chosen.
    :param str password: Password that the user has chosen.
    :param str bio: Small biography of the uesr.

    :attribute password_hash: Hashed version of the users's password.
    :attribute follower_associations: All associations to movements where the follower is this user. Useful for determining the leaders of a user.
    :attribute movements: List of all movements that the user is subscribed to.

    :todo: Make a user.leaders dictionary attribute that has movements as the keys and lists of leaders as the values. Right now this is solved with the leaders method.
    """

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32))
    email = db.Column(db.String(40), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(32))
    bio = db.Column(db.UnicodeText)

    follower_associations = db.relationship(
        "MovementUserAssociation", foreign_keys="MovementUserAssociation.follower_id"
    )

    movements = association_proxy(
        "follower_associations",
        "movement",
        creator=lambda movement: MovementUserAssociation(movement=movement),
    )

    @property
    def current_movements(self):
        # To prevent circular imports this is done here
        from .movement import Movement

        return (
            Movement.query.join(MovementUserAssociation)
            .filter(
                MovementUserAssociation.movement_id == Movement.id,
                MovementUserAssociation.follower_id == self.id,
                MovementUserAssociation.destroyed == None,
            )
            .group_by(Movement.id)
            .all()
        )

    def __init__(self, username, email, password, role="user", bio=""):
        self.username = username
        self.email = email
        self.hash_and_store_password(password)
        self.role = role
        self.bio = bio

    def __repr__(self):
        return f"<User {self.username}>"

    @classmethod
    def find_by_name(cls, query_username):
        return cls.query.filter_by(username=query_username).one_or_none()

    @classmethod
    def find_by_email(cls, query_email):
        return cls.query.filter_by(email=query_email).one_or_none()

    @classmethod
    def find_by_id(cls, id):
        return cls.query.get(id)

    def hash_and_store_password(self, password):
        """
        Hash password and set it as the password_hash.
        :param str password: Password that is to be hashed.
        """
        self.password_hash = pwd_context.hash(password)

    def get_email_hash(self):
        """
        Hash e-mail with md5.
        """
        h = hashlib.md5()
        h.update(bytes(self.email, "utf-8"))
        email_hash = h.hexdigest()
        return email_hash

    def get_password_reset_token(self):
        """
        Make a dictionary containing the id for password reset
        + an expiration timestamp such that the token is valid for 2 hours
        and encodes it into a JWT.

        :rtype str: the JWT that is used to verify the password reset.
        """
        now = datetime.datetime.now()
        valid = datetime.timedelta(hours=2)
        exp = now + valid
        exp = exp.timestamp()

        secret_key = current_app.config["SECRET_KEY"]

        token_dict = {"user_id": self.id, "exp": exp}

        token = jwt.encode(token_dict, secret_key, algorithm="HS256").decode("utf-8")
        return token

    def get_email_change_token(self, new_email):
        """
        Make a dictionary containing the user's id, new email
        + an expiration timestamp such that the token is valid for 2 hours
        and encodes it into a JWT.

        :param str new_email: The new e-mail that needs to be verified.
        :rtype str: the JWT that is used to verify the e-mail change.
        """
        now = datetime.datetime.now()
        valid = datetime.timedelta(hours=2)
        exp = now + valid
        exp = exp.timestamp()

        secret_key = current_app.config["SECRET_KEY"]

        token_dict = {"user_id": self.id, "new_email": new_email, "exp": exp}

        token = jwt.encode(token_dict, secret_key, algorithm="HS256").decode("utf-8")
        return token

    def verify_password(self, password):
        """
        Verify that this password matches with the hashed version in the database.
        :rtype bool:
        """
        return pwd_context.verify(password, self.password_hash)

    def leaders(self, movement):
        """
        Find all the leaders of this user in the provided movement.

        :param gridt.models.movement.Movement movement: The movement that the user is to retrieve the leaders from.
        """
        associations = MovementUserAssociation.query.filter(
            MovementUserAssociation.follower_id == self.id,
            MovementUserAssociation.movement_id == movement.id,
            not_(MovementUserAssociation.leader_id == None),
            MovementUserAssociation.destroyed == None,
        ).all()
        return [a.leader for a in associations]

    def dictify(self):
        return {
            "id": self.id,
            "username": self.username,
            "bio": self.bio,
            "avatar": self.get_email_hash(),
        }

    def save_to_db(self):
        """
        Save this user and all of the changes made to it to the database.
        """
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        """
        Delete this user from the database.

        :warning: This is a permanent action and cannot be undone.
        """
        db.session.delete(self)
        db.session.commit()
