import json
from gridt.tests.base_test import BaseTest
from gridt.models.user import User
from marshmallow import Schema, ValidationError
from unittest.mock import patch


class RegistrationResourceTest(BaseTest):
    def test_registration(self):
        with self.app_context():
            user_json = {
                "username": "robin",
                "email": "robin@gridt.org",
                "password": "secret",
            }

            resp = self.client.post("/register", json=user_json)

            self.assertEqual(resp.status_code, 201)
            self.assertEqual(
                resp.get_json(), {"message": "Succesfully created user."}
            )

    @patch("marshmallow.Schema.load", side_effect=ValidationError({"message": "Error."}))
    def test_registration_bad_schema(self, func):
        with self.app_context():
            resp = self.client.post("/register", json={})

            func.assert_called_with({})
            self.assertEqual(resp.status_code, 400)

    def test_logged_in(self):
        with self.app_context():
            movement = self.create_movement()
            user = self.create_user_in_movement(movement)

            resp = self.request_as_user(self.users[0], "GET", "/identity")
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(
                resp.get_json(),
                {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "bio": user.bio,
                    "avatar": user.get_email_hash(),
                },
            )
