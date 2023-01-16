import sys
import logging
import lorem
import random

from unittest import TestCase

from gridt_server.app import create_app
from gridt_server.db import db

from src.models.movement import Movement
from src.models.user import User
from src.models.signal import Signal

from sqlalchemy import create_engine
from src.db import Base, Session


# LoggedTestCase and LogThisTestCase accredited to:
# https://stackoverflow.com/a/15969985/1051438
class LogThisTestCase(type):
    def __new__(cls, name, bases, dct):
        # if the TestCase already provides setUp, wrap it
        if "setUp" in dct:
            setUp = dct["setUp"]
        else:
            setUp = lambda self: None  # noqa: E731
            print("creating setUp...")

        def wrappedSetUp(self):
            # for hdlr in self.logger.handlers:
            #    self.logger.removeHandler(hdlr)
            self.hdlr = logging.StreamHandler(sys.stdout)
            self.logger.addHandler(self.hdlr)
            setUp(self)

        dct["setUp"] = wrappedSetUp

        # same for tearDown
        if "tearDown" in dct:
            tearDown = dct["tearDown"]
        else:
            tearDown = lambda self: None  # noqa: E731

        def wrappedTearDown(self):
            tearDown(self)
            self.logger.removeHandler(self.hdlr)

        dct["tearDown"] = wrappedTearDown

        # return the class instance with the replaced setUp/tearDown
        return type.__new__(cls, name, bases, dct)


class LoggedTestCase(TestCase):
    __metaclass__ = LogThisTestCase
    logger = logging.getLogger()
    # Uncomment below to enable logging while testing
    # logger.setLevel(logging.DEBUG)


class BaseTest(LoggedTestCase):
    def setUp(self):
        app = create_app(overwrite_conf="conf/test.conf")

        # Make sure db exists
        with app.app_context():
            db.init_app(app)
            db.create_all()
        # Get a test client
        self.app = app
        self.client = app.test_client()
        self.app_context = app.app_context

        self.users = []
        self.movements = []

        engine = create_engine(app.config["SQLALCHEMY_DATABASE_URI"])
        Session.configure(bind=engine)
        Base.metadata.create_all(engine)

    def tearDown(self):
        # Make database blank
        with self.app_context():
            db.session.remove()
            db.drop_all()

    def obtain_token(self, email, password):
        resp = self.client.post(
            "/auth",
            json={"username": email, "password": password},
            headers={"Content-Type": "application/json"},
        )
        token = resp.get_json()["access_token"]

        return token

    def create_user(self, generate_bio=False):
        username = lorem.sentence()
        email = f"{lorem.sentence().replace(' ', '').replace('.', '')}@test.com"
        password = lorem.sentence()
        bio = ""

        if generate_bio:
            bio = lorem.paragraph()

        user = User(username, email, password, role="user", bio=bio)

        user.save_to_db()

        user_dict = {
            "id": user.id,
            "username": username,
            "email": email,
            "bio": bio,
            "password": password,
            "avatar": user.get_email_hash(),
        }
        self.users.append(user_dict)

        return user

    def create_movement(self):
        name = lorem.sentence().split()[0]
        movement = Movement(
            name,
            random.choice(["daily", "twice daily", "weekly"]),
            lorem.sentence(),
            lorem.paragraph(),
        )

        movement.save_to_db()
        self.movements.append(movement)

        return movement

    def create_user_in_movement(self, movement, generate_bio=False):
        if movement not in self.movements:
            raise ValueError("Movement not registered")
        user = self.create_user(generate_bio)
        movement.add_user(user)
        return user

    def request_as_user(self, user_dict, request_type, *args, **kwargs):
        token = user_dict.get("token", None)
        if not token:
            token = self.obtain_token(user_dict["email"], user_dict["password"])
            user_dict["token"] = token

        kwargs["headers"] = {"Authorization": f"JWT {token}"}

        if request_type == "GET":
            return self.client.get(*args, **kwargs)
        elif request_type == "POST":
            return self.client.post(*args, **kwargs)
        elif request_type == "PUT":
            return self.client.put(*args, **kwargs)
        elif request_type == "DELETE":
            return self.client.delete(*args, **kwargs)
        else:
            raise ValueError(f'"{request_type}" is not a known request type.')

    def signal_as_user(self, user_dict, movement, message=None):
        leader = User.find_by_name(user_dict["username"])

        signal = Signal(leader, movement, message)
        signal.save_to_db()
        return signal

    def get_user(self, index):
        user_dict = self.users[index]
        return User.find_by_id(user_dict["id"])
