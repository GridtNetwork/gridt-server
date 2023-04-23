from unittest.mock import patch
from flask_jwt_extended import jwt_required
from flask_restful import Resource

from gridt_server.tests.base_test import BaseTest


class LoginTest(BaseTest):
    class DummyResource(Resource):
        """
        Dummy resource for testing purposes
        """
        @jwt_required()
        def get(self):
            return "Hello World!"

    def setUp(self):
        super(LoginTest, self).setUp()
        self.api.add_resource(self.DummyResource, '/dummy')

    def tearDown(self):
        super(LoginTest, self).tearDown()

    @patch(
        "gridt_server.resources.login.verify_password_for_email",
        return_value=42
    )
    def test_login_success(self, mock_verify):
        with self.app_context():
            self.assertEqual(self.client.get("/dummy").status_code, 401)

            response_1 = self.client.post(
                "/auth",
                headers={"Content-Type": "application/json"},
                json={"username": "good@email.com", "password": "correct"},
            )

            self.assertEqual(response_1.status_code, 200)

            token = response_1.get_json()["access_token"]
            headers = {"Authorization": f"JWT {token}"}

            response_2 = self.client.get("/dummy", headers=headers)
            self.assertEqual(response_2.status_code, 200)
            self.assertEqual(response_2.data, b'"Hello World!"\n')

        mock_verify.assert_called_once_with("good@email.com", "correct")
