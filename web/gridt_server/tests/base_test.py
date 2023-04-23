import sys
import logging

from unittest import TestCase

from gridt_server.app import load_config, register_api_endpoints

from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token
from flask_restful import Api


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
        self.app = Flask(__name__)
        load_config(self.app, overwrite_conf="../conf/test.conf")
        self.app.config["JWT_HEADER_TYPE"] = "JWT"

        self.api = Api(self.app)
        register_api_endpoints(self.api)
        self.jwt = JWTManager(self.app)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context

    def obtain_token_header(self, user_id):
        return f"JWT {create_access_token(user_id)}"

    def create_user(self, generate_bio=False):
        raise NotImplementedError

    def create_movement(self):
        raise NotImplementedError

    def create_user_in_movement(self, movement, generate_bio=False):
        raise NotImplementedError

    def request_as_user(self, user_dict, request_type, *args, **kwargs):
        raise NotImplementedError

    def signal_as_user(self, user_dict, movement, message=None):
        raise NotImplementedError

    def get_user(self, index):
        raise NotImplementedError
