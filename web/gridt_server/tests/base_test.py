import sys
import logging
import lorem
import random

from unittest import TestCase

from gridt_server.app import create_app

from sqlalchemy import create_engine
from gridt.db import Base, Session


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
        # Get a test client
        self.app = app
        self.client = app.test_client()
        self.app_context = app.app_context
    
    def tearDown(self):
        pass
