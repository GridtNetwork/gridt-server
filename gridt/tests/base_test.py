import os
import logging
import json
from unittest import TestCase

from gridt.app import create_app
from gridt.db import db

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
        app = create_app(overwrite_conf="test")

        # Make sure db exists
        with app.app_context():
            db.init_app(app)
            db.create_all()
        # Get a test client
        self.app = app
        self.client = app.test_client()
        self.app_context = app.app_context

    def tearDown(self):
        # Make database blank
        with self.app_context():
            db.session.remove()
            db.drop_all()

    def obtain_token(self, username, password):
        resp = self.client.post(
            "/auth",
            json={"username": username, "password": password},
            headers={"Content-Type": "application/json"},
        )
        data = resp.data.decode("utf-8")
        token = json.loads(data)["access_token"]

        return token
