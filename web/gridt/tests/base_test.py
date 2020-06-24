import os
import logging
import json
import lorem
import random

from unittest import TestCase
from unittest.mock import patch

from gridt.app import create_app
from gridt.db import db

from gridt.models.movement import Movement
from gridt.models.user import User
from gridt.models.signal import Signal

# LoggedTestCase and LogThisTestCase accredited to:
# https://stackoverflow.com/a/15969985/1051438
class LogThisTestCase(type):
    def __new__(cls, name, bases, dct):
        # if the TestCase already provides setUp, wrap it
        if "setUp" in dct:
            setUp = dct["setUp"]
        else:
            setUp = lambda self: None
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
            tearDown = lambda self: None

        def wrappedTearDown(self):
            tearDown(self)
            self.logger.removeHandler(self.hdlr)

        dct["tearDown"] = wrappedTearDown

        # return the class instance with the replaced setUp/tearDown
        return type.__new__(cls, name, bases, dct)


class LoggedTestCase(TestCase):
    __metaclass__ = LogThisTestCase
    logger = logging.getLogger()
    ## Uncomment below to enable logging while testing
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
        data = resp.data.decode("utf-8")
        token = json.loads(data)["access_token"]

        return token

    def create_user(self, generate_bio=False):
        username = lorem.sentence()
        email = lorem.sentence()
        password = lorem.sentence()
        bio = ""

        if bio:
            bio = lorem.paragraph()

        user = User(username, email, password, role="user")

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

    def signal_as_user(self, user_dict, movement, message=None, moment=None):
        leader = User.find_by_name(user_dict["username"])

        if moment:
            with patch("gridt.models.signal.Signal._get_now") as now:
                now.return_value = moment
                signal = Signal(leader, movement, message)
                signal.save_to_db()
                return signal
        else:
            signal = Signal(leader, movement, message)
            signal.save_to_db()
            return signal

    def get_user(self, index):
        user_dict = self.users[index]
        return User.find_by_id(user_dict["id"])
