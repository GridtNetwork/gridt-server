from unittest.mock import patch
from flask_jwt_extended import jwt_required

from gridt_server.tests.base_test import BaseTest


class LoginTest(BaseTest):
    # patch verify_password_for_email, return_value=1
    # patch create_access_token, return_value="foo"
    def test_login(self, func):
        with self.app_context():
            response = self.client.post(
                "/auth",
                headers={"Content-Type": "application/json"},
                json={"username": "test@test.com", "password": "password"},
            )

            token = response.get_json()["access_token"]
            # self.assertEqual(token, "foo")
            resp = self.client.get("/test", headers={"Authorization": f"JWT {token}"})

            self.assertEqual(resp.status_code, 200)
            # assert that create_access_token has been called

    # Login with bad username and password
    # verify_password_for_email needs to have ValueError side-effect
