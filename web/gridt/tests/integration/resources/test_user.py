import lorem
import json
import os

from flask import current_app
from freezegun import freeze_time
import datetime

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

    def test_change_password_with_no_password(self):
        with self.app_context():
            user = self.create_user()

            resp = self.request_as_user(
                self.users[0], "POST", "/change_password", json={}
            )

            self.assertIn("message", resp.get_json())
            self.assertEqual(resp.status_code, 400)

            resp = self.request_as_user(
                self.users[0],
                "POST",
                "/change_password",
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
                "/change_password",
                json={
                    "old_password": "gibberish",
                    "new_password": "somethingyoullneverguess",
                },
            )

            self.assertIn("message", resp.get_json())
            self.assertEqual(resp.status_code, 400)

    def test_change_password_with_correct_password(self):
        # json should contain old_password (self.users[0]["password"]) and new password
        with self.app_context():
            user = self.create_user()

            resp = self.request_as_user(
                self.users[0],
                "POST",
                "/change_password",
                json={
                    "old_password": self.users[0]["password"],
                    "new_password": "somethingyoullneverguess"
                },
            )

            self.assertIn("message", resp.get_json())
            self.assertEqual(resp.status_code, 200)
            self.assertTrue(user.verify_password("somethingyoullneverguess"))

    def test_no_api_key(self):
        # This test doesn't currently do anything since EMAIL_API_KEY is
        # currently not in the conf files but taken from environment values
        with self.app_context():
            email = "any@email.com"
            current_app.config["EMAIL_API_KEY"] = None

            resp = self.client.post(
                "/request_password_reset",
                json={
                    "email": email
                },
            )

            self.assertIn("message", resp.get_json())
            self.assertEqual(resp.status_code, 500)
    
    @patch("util.send_email", return_value=True)
    def test_send_password_reset_email_wrong(self, func):
        with self.app_context():
            # Make a request with nonexistent e-mail
            email = "nonexistent@email.com"
            
            resp = self.client.post(
                "/request_password_reset",
                json={
                    "email": email
                },
            )

            # Test that email will not get sent
            func.assertNotCalled()

            # In order to not give away sensitive information
            # message must be the same as a successful attempt
            self.assertIn("message", resp.get_json())
            self.assertEqual(resp.status_code, 200)

    @patch("util.send_email", return_value=True)
    def test_send_password_reset_email_correct(self, func):
        # Request reset password, e-mail in database
        with self.app_context():
            user = self.create_user()

            resp = self.client.post(
                "/request_password_reset",
                json={
                    "email": user.email
                },
            )

            token = user.get_password_reset_token()
            link = f"https://app.gridt.org/reset_password?token={token}"
            subj = "Reset your password"
            body = f"Your password has been reset, please follow the following link: {link}"
            # Test that email will get sent
            func.assertCalledWith(user.email, subj, body)
            self.assertIn("message", resp.get_json())
            self.assertEqual(resp.status_code, 200)

    def test_reset_password_token_correct(self):
        with self.app_context():
            user = self.create_user()
            token = user.get_password_reset_token()

            resp = self.client.post(
                "/reset_password",
                json={
                    "token": token,
                    "password": "testpass"
                }
            )

            self.assertIn("message", resp.get_json())
            self.assertEqual(resp.status_code, 200)
            self.assertTrue(user.verify_password("testpass"))


    def test_reset_password_token_expired(self):
        with self.app_context():
            user = self.create_user()
            with freeze_time("2020-04-18 22:10:00"):
                token = user.get_password_reset_token()

            with freeze_time("2020-04-19 00:10:01"):
                resp = self.client.post(
                    "/reset_password",
                    json={
                        "token": token,
                        "password": "testpass"
                    }
                )
            
                self.assertIn("message", resp.get_json())
                self.assertEqual(resp.status_code, 400)

    def test_password_reset_token_tampered(self):
        with self.app_context():
            user = self.create_user()
            token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9." \
                "eyJpZCI6MSwiZXhwIjoxNTg3MzM0MjAwfW." \
                "2qdnq1_YJS9tgKVlIVpBbaAanyxQnCyVmV6s7QcOuBo"

            resp = self.client.post(
                "/reset_password",
                json={
                    "token": token,
                    "password": "testpass"
                }
            )
        
            self.assertIn("message", resp.get_json())
            self.assertEqual(resp.status_code, 400)