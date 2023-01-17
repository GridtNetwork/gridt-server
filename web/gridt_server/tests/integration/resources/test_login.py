from unittest.mock import patch
from flask_jwt_extended import jwt_required

from gridt_server.tests.base_test import BaseTest

class LoginTest(BaseTest):
    @patch("flask_jwt_extended.create_access_token", return_value="mock token")
    def test_login(self, func):
        with self.app_context():
            user = User("username", "test@test.com", "password")
            user.save_to_db()

            @self.app.route("/test")
            @jwt_required
            def test_route():
                return "Hello World!"

            self.assertEqual(self.client.get("/test").status_code, 401)

            response = self.client.post(
                "/auth",
                headers={"Content-Type": "application/json"},
                json={"username": "test@test.com", "password": "password"},
            )

            token = response.get_json()["access_token"]
            resp = self.client.get("/test", headers={"Authorization": f"JWT {token}"})

            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.data, b"Hello World!")
