import lorem
import json

from flask import current_app
from freezegun import freeze_time
import datetime

from gridt.tests.base_test import BaseTest
from gridt.models.user import User
from gridt.resources.user import (
    BioResource,
    ChangePasswordResource,
    RequestPasswordResetResource
)


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
        # (Temporarily) override email API key
        # Expect that error message is displayed
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
    
    def test_send_reset_password_email_wrong(self):
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


            # In order to not give away sensitive information
            # message must be the same as a successful attempt
            # self.assertIn("message", resp.get_json())
            # self.assertEqual(resp.status_code, 200)


    def test_send_reset_password_email_correct(self):
        # Request reset password, e-mail in database
        with self.app_context():
            user = self.create_user()

            resp = self.client.post(
                "/request_password_reset",
                json={
                    "email": user.email
                },
            )

            # Test that email will get sent

            # self.assertIn("message", resp.get_json())
            # self.assertEqual(resp.status_code, 200)

    def test_password_reset_token_correct(self):
        with self.app_context():
            user = self.create_user()
            token = user.get_password_reset_token()

            resp = self.client.post(
                "/reset_password",
                json={
                    "token": token,
                    "password": "testpass",
                    "password2": "testpass"
                }
            )

            self.assertIn("message", resp.get_json())
            self.assertEqual(resp.status_code, 200)
            self.assertTrue(user.verify_password("testpass"))

    def test_password_reset_no_match(self):
        with self.app_context():
            user = self.create_user()
            token = user.get_password_reset_token()
            print(token)

            resp = self.client.post(
                "/reset_password",
                json={
                    "token": token,
                    "password": "testpass1",
                    "password2": "testpass2"
                }
            )

            self.assertIn("message", resp.get_json())
            self.assertEqual(resp.status_code, 400)


    def test_password_reset_token_expired(self):
        with self.app_context():
            user = self.create_user()
            with freeze_time("2020-04-18 22:10:00"):
                token = user.get_password_reset_token()
                print(token)

            # User uses expired token
            with freeze_time("2020-04-19 22:10:00"):
                resp = self.client.post(
                    "/reset_password",
                    json={
                        "token": token,
                        "password": "testpass",
                        "password": "testpass"
                    }
                )
            
                self.assertIn("message", resp.get_json())
                self.assertEqual(resp.status_code, 400)

    # def test_password_reset_token_tampered(self):
    #     with self.app_context():
    #         user = self.create_user()
    #         token_dict = {
    #             "reset_password": 1,
    #             "exp": exp
    #         }

    #         resp = self.client.post(
    #             "/reset_password",
    #             json={
    #                 "token": token,
    #                 "password": "testpass",
    #                 "password": "testpass"
    #             }
    #         )


    def test_password_reset_token_nonexistent_user(self):
        with self.app_context():
            user = self.create_user()
            token = user.get_password_reset_token()
            user.delete_from_db

            resp = self.client.post(
                "/reset_password",
                json={
                    "token": token,
                    "password": "testpass",
                    "password": "testpass"
                }
            )

            self.assertIn("message", resp.get_json())
            self.assertEqual(resp.status_code, 400)