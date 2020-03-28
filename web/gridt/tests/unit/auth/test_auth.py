import sys
import base64
import logging
import unittest
import json

from flask import current_app
from flask_jwt import jwt_required

from gridt.tests.base_test import BaseTest
from gridt.models.user import User
from gridt.auth import security


class AuthTest(BaseTest):
    def test_verify(self):
        with self.app_context():
            user = User("username", "test@test.com", "password")
            user.save_to_db()

            @self.app.route("/test")
            @jwt_required()
            def test_route():
                return "Hello World!"

            self.assertEqual(self.client.get("/test").status_code, 401)

            response = self.client.post(
                "/auth",
                headers={"Content-Type": "application/json"},
                json={"username": "test@test.com", "password": "password"},
            )

            data = json.loads(response.data)
            token = data["access_token"]
            resp = self.client.get("/test", headers={"Authorization": f"JWT {token}"})

            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.data, b"Hello World!")
