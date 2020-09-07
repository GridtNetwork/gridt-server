import json
from gridt.tests.base_test import BaseTest
from gridt.models.user import User


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
                json.loads(resp.data), {"message": "Succesfully created user."}
            )

    def test_logged_in(self):
        with self.app_context():
            movement = self.create_movement()
            user = self.create_user_in_movement(movement)

            resp = self.request_as_user(self.users[0], "GET", "/identity")
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(
                json.loads(resp.data),
                {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "bio": user.bio,
                    "avatar": user.get_email_hash(),
                },
            )
