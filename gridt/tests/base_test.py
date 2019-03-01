import os
from unittest import TestCase

from app import create_app
from db import db

class BaseTest(TestCase):
    def setUp(self):
        app = create_app(overwrite_conf="testing")

        self.assertEqual(app.config["SQLALCHEMY_DATABASE_URI"], "sqlite://")

        # Make sure db exists
        with app.app_context():
            db.init_app(app)
            db.create_all()
        # Get a test client
        self.app = app.test_client()
        self.app_context = app.app_context

    def tearDown(self):
        # Make database blank
        with self.app_context():
            db.session.remove()
            db.drop_all()
