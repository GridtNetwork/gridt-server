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
                json.loads(resp.data), {"message": "Succesfully created user"}
            )

    def test_logged_in(self):
        with self.app_context():
            user = User("robin", "robin@gridt.org", "secret")
            user.save_to_db()

            token = json.loads(
                self.client.post(
                    "/auth",
                    json={"username": "robin", "password": "secret"},
                    headers={"Content-Type": "application/json"},
                ).data
            )["access_token"]

            resp = self.client.get(
                "/logged_in", headers={"Authorization": f"JWT {token}"}
            )
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(
                json.loads(resp.data), {"message": "Hi robin, you are logged in."}
            )
