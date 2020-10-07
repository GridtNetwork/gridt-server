import lorem
import json
import os

from flask import current_app
from freezegun import freeze_time

from marshmallow import ValidationError

from gridt_server.tests.base_test import BaseTest
from gridt_server.models.user import User
from gridt_server.db import db

from unittest.mock import patch


class UserResourceTest(BaseTest):
    def test_update_bio(self):
        with self.app_context():
            new_bio = lorem.paragraph()

            user = self.create_user(generate_bio=True)

            resp = self.request_as_user(
                self.users[0], "PUT", "/bio", json={"bio": new_bio}
            )

            # Reload user
            db.session.expunge_all()
            user = User.query.get(1)

            self.assertEqual(resp.get_json(), {"message": "Bio successfully changed."})
            self.assertEqual(user.bio, new_bio)

    def test_update_bio_improperly(self):
        with self.app_context():
            self.create_user(generate_bio=True)

            resp = self.request_as_user(self.users[0], "PUT", "/bio", json={})

            self.assertEqual(
                resp.get_json(), {"message": "bio: Missing data for required field."},
            )

    def test_change_password_with_no_password(self):
        with self.app_context():
            self.create_user()

            resp = self.request_as_user(
                self.users[0], "POST", "/user/change_password", json={}
            )

            self.assertIn("message", resp.get_json())
            self.assertEqual(resp.status_code, 400)

            resp = self.request_as_user(
                self.users[0],
                "POST",
                "/user/change_password",
                json={"old_password": self.users[0]["password"]},
            )

            self.assertIn("message", resp.get_json())
            self.assertEqual(resp.status_code, 400)

    def test_change_password_with_wrong_password(self):
        with self.app_context():
            user = self.create_user()

            resp = self.request_as_user(
                self.users[0],
                "POST",
                "/user/change_password",
                json={
                    "old_password": "gibberish",
                    "new_password": "somethingyoullneverguess",
                },
            )

            self.assertIn("message", resp.get_json())
            self.assertEqual(resp.status_code, 400)

    @patch("gridt.util.email_templates.send_email", return_value=True)
    @patch.dict(
        os.environ,
        {
            "PASSWORD_CHANGE_NOTIFICATION_TEMPLATE": "mytemp",
            "EMAIL_API_KEY": "random key",
        },
    )
    def test_change_password_with_correct_password(self, func):
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

            template_data = {
                "link": "https://app.gridt.org/user/reset_password/request"
            }

            # Reload user changed by gridtlib
            db.session.expunge_all()
            user = User.query.get(1)

            self.assertIn("message", resp.get_json())
            self.assertEqual(resp.status_code, 200)
            self.assertTrue(user.verify_password("somethingyoullneverguess"))
            func.assert_called_with(user.email, "mytemp", template_data)

    def test_no_api_key(self):
        with self.app_context():
            email = "any@email.com"
            current_app.config["EMAIL_API_KEY"] = None

            resp = self.client.post(
                "/user/reset_password/request", json={"email": email},
            )

            self.assertIn("message", resp.get_json())
            self.assertEqual(resp.status_code, 500)

    @patch("gridt.controllers.user.logging.critical")
    @patch("util.email_templates.send_email", return_value=True)
    def test_send_password_reset_email_wrong(self, email_func, log_func):
        with self.app_context():
            # Make a request with nonexistent e-mail
            email = "nonexistent@email.com"

            resp = self.client.post(
                "/user/reset_password/request", json={"email": email},
            )

            # Test that email will not get sent
            email_func.assert_not_called()

            # In order to not give away sensitive information
            # message must be the same as a successful attempt
            self.assertIn("message", resp.get_json())
            self.assertEqual(resp.status_code, 200)

    @freeze_time("2020-08-25 17:19:00")
    @patch.dict("os.environ", {"PASSWORD_RESET_TEMPLATE": "random key"})
    @patch("gridt.util.email_templates.send_email", return_value=True)
    def test_send_password_reset_email_correct(self, func):
        # Request reset password, e-mail in database
        with self.app_context():
            user = self.create_user()

            resp = self.client.post(
                "/user/reset_password/request", json={"email": user.email},
            )

            token = user.get_password_reset_token()

            template_data = {
                "link": f"https://app.gridt.org/user/reset_password/confirm?token={token}"
            }

            func.assert_called_with(user.email, "random key", template_data)
            self.assertIn("message", resp.get_json())
            self.assertEqual(resp.status_code, 200)

    @patch("util.email_templates.send_email", return_value=True)
    def test_reset_password_token_correct(self, func):
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

    def test_reset_password_token_expired(self):
        with self.app_context():
            user = self.create_user()
            with freeze_time("2020-04-18 22:10:00"):
                token = user.get_password_reset_token()

            with freeze_time("2020-04-19 00:10:01"):
                resp = self.client.post(
                    "/user/reset_password/confirm",
                    json={"token": token, "password": "testpass"},
                )

                self.assertIn("message", resp.get_json())
                self.assertEqual(resp.status_code, 400)

    def test_reset_password_token_expired2(self):
        with self.app_context():
            user = self.create_user()
            with freeze_time("2020-04-18 22:10:00"):
                token = user.get_password_reset_token()

            with freeze_time("2020-04-19 00:10:01"):
                resp = self.client.post(
                    "/user/reset_password/confirm",
                    json={"token": token, "password": "testpass"},
                )

                self.assertIn("message", resp.get_json())
                self.assertEqual(resp.status_code, 400)

    def test_password_reset_token_tampered(self):
        with self.app_context():
            user = self.create_user()
            token = (
                "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
                "eyJpZCI6MSwiZXhwIjoxNTg3MzM0MjAwfW."
                "2qdnq1_YJS9tgKVlIVpBbaAanyxQnCyVmV6s7QcOuBo"
            )

            resp = self.client.post(
                "/user/reset_password/confirm",
                json={"token": token, "password": "testpass"},
            )

            self.assertIn("message", resp.get_json())
            self.assertEqual(resp.status_code, 400)

    @patch("gridt.util.email_templates.send_email", return_value=True)
    @patch.dict(
        os.environ, {"EMAIL_CHANGE_TEMPLATE": "random key"},
    )
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

                template_data = {
                    "username": user.username,
                    "link": f"https://app.gridt.org/user/change_email/confirm?token={token}",
                }

                func.assert_called_with(new_email, "random key", template_data)
                self.assertIn("message", resp.get_json())
                self.assertEqual(resp.status_code, 200)

    @patch("gridt.controllers.user.logging.critical")
    @patch("util.email_templates.send_email", return_value=True)
    def test_request_email_change_existing_email(self, email_func, log_func):
        with self.app_context():
            self.create_user()
            self.create_user()

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
            email_func.assert_not_called()

    @patch(
        "gridt_server.resources.user.RequestEmailChangeResource.schema.load",
        side_effect=ValidationError({"message": "Error."}),
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

    @patch("gridt.util.email_templates.send_email", return_value=True)
    @patch.dict("os.environ", {"EMAIL_CHANGE_NOTIFICATION_TEMPLATE": "random key"})
    def test_change_email_proper_schema(self, func):
        with self.app_context():
            user = self.create_user()
            new_email = "new@email.com"
            token = user.get_email_change_token(new_email)

            resp = self.client.post("/user/change_email/confirm", json={"token": token})

            template_data = {"username": user.username}

            # Reload user from database because of conflicting sessions.
            db.session.expunge_all()
            user = User.query.get(1)

            self.assertIn("message", resp.get_json())
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(user.email, "new@email.com")
            func.assert_called_with(user.email, "random key", template_data)

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
