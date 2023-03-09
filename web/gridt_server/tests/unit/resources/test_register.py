from unittest.mock import patch

from gridt_server.tests.base_test import BaseTest


class RegistrationResourceTest(BaseTest):
    user_id = 42
    username = "robin"
    email = "robin@gridt.org"
    password = "secret"

    @patch(
        "gridt_server.resources.register.register"
    )
    def test_registration(self, mock_register):
        with self.app_context():
            user_json = {
                "username": self.username,
                "email": self.email,
                "password": self.password,
            }

            response = self.client.post("/register", json=user_json)

            self.assertEqual(response.status_code, 201)
            self.assertEqual(
                response.get_json(), {"message": "Succesfully created user."}
            )

        mock_register.assert_called_once_with(
            self.username, self.email, self.password
        )

    @patch(
        "gridt_server.resources.register.get_identity",
        return_value={
            "id": user_id,
            "username": username,
            "bio": "bio",
            "avatar": "email_hash",
            "email": email
        }
    )
    def test_logged_in(self, mock_get_identity):
        with self.app_context():
            headers = {"Authorization": self.obtain_token_header(self.user_id)}
            response = self.client.get("/identity", headers=headers)
            self.assertEqual(response.status_code, 200)
            self.assertDictEqual(
                response.get_json(),
                {
                    "id": self.user_id,
                    "username": self.username,
                    "email": self.email,
                    "bio": "bio",
                    "avatar": "email_hash"
                },
            )

        mock_get_identity.assert_called_once_with(42)
