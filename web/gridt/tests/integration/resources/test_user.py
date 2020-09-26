import lorem
import json
import os

from flask import current_app
from freezegun import freeze_time
import datetime

from marshmallow import Schema, ValidationError

from gridt.tests.base_test import BaseTest
from gridt.models.user import User

from unittest.mock import patch


class UserResourceTest(BaseTest):
    def test_update_bio(self):
        with self.app_context():
            new_bio = lorem.paragraph()

            user = self.create_user(generate_bio=True)

            resp = self.request_as_user(
                self.users[0], "PUT", "/bio", json={"bio": new_bio}
            )

            self.assertEqual(resp.get_json(), {"message": "Bio successfully changed."})
            self.assertEqual(user.bio, new_bio)

    def test_update_bio_improperly(self):
        with self.app_context():
            user = self.create_user(generate_bio=True)

            resp = self.request_as_user(self.users[0], "PUT", "/bio", json={})

            self.assertEqual(resp.get_json(), {"message": "Bad request."})

    @patch("util.email_templates.send_email", return_value=True)
    def test_change_password_successfully(self, func):
        with self.app_context():
            user = self.create_user()

            resp = self.request_as_user(
                self.users[0],
                "POST",
                "/user/change_password",
                json={
                    "old_password": self.users[0]["password"],
                    "new_password": "somethingyoullneverguess",
                },
            )

            template_id = current_app.config["PASSWORD_CHANGE_NOTIFICATION_TEMPLATE"]
            template_data = {
                "link": "https://app.gridt.org/user/reset_password/request"
            }

            self.assertIn("message", resp.get_json())
            self.assertEqual(resp.status_code, 200)
            self.assertTrue(user.verify_password("somethingyoullneverguess"))
            func.assert_called_with(user.email, template_id, template_data)

    @patch(
        "marshmallow.Schema.load", side_effect=ValidationError({"message": "Error."})
    )
    def test_change_password_bad_schema(self, func):
        with self.app_context():
            user = self.create_user()

            resp = self.request_as_user(
                self.users[0], "POST", "/user/change_password", json={},
            )

            func.assert_called_with({})
            self.assertEqual(resp.status_code, 400)

    def test_no_api_key(self):
        with self.app_context():
            email = "any@email.com"
            current_app.config["EMAIL_API_KEY"] = None

            resp = self.client.post(
                "/user/reset_password/request", json={"email": email},
            )

            self.assertIn("message", resp.get_json())
            self.assertEqual(resp.status_code, 500)

    @patch("util.email_templates.send_email", return_value=True)
    def test_send_password_reset_email_wrong(self, func):
        with self.app_context():
            # Make a request with nonexistent e-mail
            email = "nonexistent@email.com"

            resp = self.client.post(
                "/user/reset_password/request", json={"email": email},
            )

            # Test that email will not get sent
            func.assert_not_called()

            # In order to not give away sensitive information
            # message must be the same as a successful attempt
            self.assertIn("message", resp.get_json())
            self.assertEqual(resp.status_code, 200)

    @freeze_time("2020-08-25 17:19:00")
    @patch("util.email_templates.send_email", return_value=True)
    def test_send_password_reset_email_correct(self, func):
        # Request reset password, e-mail in database
        with self.app_context():
            user = self.create_user()

            resp = self.client.post(
                "/user/reset_password/request", json={"email": user.email},
            )

            token = user.get_password_reset_token()

            template_id = current_app.config["PASSWORD_RESET_TEMPLATE"]
            template_data = {
                "link": f"https://app.gridt.org/user/reset_password/confirm?token={token}"
            }

            func.assert_called_with(user.email, template_id, template_data)
            self.assertIn("message", resp.get_json())
            self.assertEqual(resp.status_code, 200)

    @patch("util.email_templates.send_email", return_value=True)
    def test_reset_password_correctly(self, func):
        with self.app_context():
            user = self.create_user()
            token = user.get_password_reset_token()

            resp = self.client.post(
                "/user/reset_password/confirm",
                json={"token": token, "password": "testpass"},
            )

            template_id = current_app.config["PASSWORD_CHANGE_NOTIFICATION_TEMPLATE"]
            template_data = {
                "link": "https://app.gridt.org/user/reset_password/request"
            }

            self.assertIn("message", resp.get_json())
            self.assertEqual(resp.status_code, 200)
            self.assertTrue(user.verify_password("testpass"))
            func.assert_called_with(user.email, template_id, template_data)

    @patch(
        "marshmallow.Schema.load", side_effect=ValidationError({"message": "Error."})
    )
    def test_reset_password_bad_schema(self, func):
        with self.app_context():
            user = self.create_user()

            resp = self.client.post("/user/reset_password/confirm", json={})

            func.assert_called_with({})
            self.assertEqual(resp.status_code, 400)

    @patch("util.email_templates.send_email", return_value=True)
    def test_request_email_change_correct(self, func):
        with self.app_context():
            user = self.create_user()
            new_email = "new@email.com"
            with freeze_time("2020-04-18 22:10:00"):
                resp = self.request_as_user(
                    self.users[0],
                    "POST",
                    "/user/change_email/request",
                    json={
                        "password": self.users[0]["password"],
                        "new_email": new_email,
                    },
                )

                token = user.get_email_change_token(new_email)

                template_id = current_app.config["EMAIL_CHANGE_TEMPLATE"]
                template_data = {
                    "username": user.username,
                    "link": f"https://app.gridt.org/user/change_email/confirm?token={token}",
                }

                func.assert_called_with(new_email, template_id, template_data)
                self.assertIn("message", resp.get_json())
                self.assertEqual(resp.status_code, 200)

    @patch("util.email_templates.send_email", return_value=True)
    def test_request_email_change_existing_email(self, func):
        with self.app_context():
            user1 = self.create_user()
            user2 = self.create_user()

            resp = self.request_as_user(
                self.users[0],
                "POST",
                "/user/change_email/request",
                json={
                    "password": self.users[0]["password"],
                    "new_email": self.users[1]["email"],
                },
            )

            self.assertIn("message", resp.get_json())
            self.assertEqual(resp.status_code, 200)
            func.assert_not_called()

    @patch(
        "marshmallow.Schema.load", side_effect=ValidationError({"message": "Error."})
    )
    def test_request_email_change_bad_schema(self, func):
        with self.app_context():
            user = self.create_user()
            new_email = "new@email.com"

            resp = self.request_as_user(
                self.users[0], "POST", "/user/change_email/request", json={},
            )

            func.assert_called_with({})
            self.assertEqual(resp.status_code, 400)

    @patch("util.email_templates.send_email", return_value=True)
    def test_change_email_proper_schema(self, func):
        with self.app_context():
            user = self.create_user()
            new_email = "new@email.com"
            token = user.get_email_change_token(new_email)

            resp = self.client.post("/user/change_email/confirm", json={"token": token})

            template_id = current_app.config["EMAIL_CHANGE_NOTIFICATION_TEMPLATE"]
            template_data = {"username": user.username}

            self.assertIn("message", resp.get_json())
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(user.email, "new@email.com")
            func.assert_called_with(user.email, template_id, template_data)

    @patch(
        "marshmallow.Schema.load",
        return_value=True,
        side_effect=ValidationError({"message": "Error."}),
    )
    def test_change_email_bad_schema(self, func):
        with self.app_context():
            user = self.create_user()
            new_email = "new@email.com"

            resp = self.client.post("/user/change_email/confirm", json={})

            func.assert_called_with({})
            self.assertEqual(resp.status_code, 400)
