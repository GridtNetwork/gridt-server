import lorem
import json
import os

from flask import current_app
from freezegun import freeze_time

from marshmallow import ValidationError

from gridt_server.tests.base_test import BaseTest

from unittest.mock import patch

# make different classes for each resource tested

class UserResourceTest(BaseTest):

    # patch mock jwt_required
    def test_update_bio(self):
        with self.app_context():
            new_bio = lorem.paragraph()
            resp = self.request_as_user(
                self.users[0], "PUT", "/bio", json={"bio": new_bio}
            ) # change to self.client.put
            self.assertEqual(resp.get_json(), {"message": "Bio successfully changed."})
            # Check that update_user_bio is called

    # patch mock jwt_required
    def test_change_password_with_correct_password(self):
        with self.app_context():

            resp = self.request_as_user(
                self.users[0],
                "POST",
                "/user/change_password",
                json={
                    "old_password": self.users[0]["password"],
                    "new_password": "somethingyoullneverguess",
                },
            )  # change to self.client.post

            self.assertIn("message", resp.get_json())
            self.assertEqual(resp.status_code, 200)
            # Check that change_password is called

    def test_no_api_key(self):
        with self.app_context():
            email = "any@email.com"
            current_app.config["EMAIL_API_KEY"] = None

            resp = self.client.post(
                "/user/reset_password/request", json={"email": email},
            )

            self.assertIn("message", resp.get_json())
            self.assertEqual(resp.status_code, 500)

    # patch mock jwt_required
    def test_reset_password_token_correct(self):
        with self.app_context():

            resp = self.client.post(
                "/user/reset_password/confirm",
                json={"token": token, "password": "testpass"},
            )

            self.assertIn("message", resp.get_json())
            self.assertEqual(resp.status_code, 200)
            # Check that reset_password is called

    # patch mock jwt_required
    def test_request_email_change_correct(self):
        with self.app_context():
            new_email = "new@email.com"
            with freeze_time("2020-04-18 22:10:00"):
                # self.users[0] needs to be fixed
                resp = self.request_as_user(
                    self.users[0],
                    "POST",
                    "/user/change_email/request",
                    json={
                        "password": self.users[0]["password"],
                        "new_email": new_email,
                    },
                ) # change to self.client.post

                self.assertIn("message", resp.get_json())
                self.assertEqual(resp.status_code, 200)
                # Check that request_email_change is called

    # patch
    def test_change_email_proper_schema(self, func):
        with self.app_context():
            token = "foo"

            resp = self.client.post("/user/change_email/confirm", json={"token": token})
            # test that change_email is called with the token.