from unittest.mock import patch

from gridt_server.tests.base_test import BaseTest


class RegistrationResourceTest(BaseTest):
    resource_path = 'gridt_server.resources.register'

    user_id = 42
    username = "robin"
    email = "robin@gridt.org"
    password = "secret"

    def send_register_request(self, key=None):
        user_json = dict(
            username=self.username,
            email=self.email,
            password=self.password,
            admin_key=key,
        )
        if key is None:
            del user_json["admin_key"]
        response = self.client.post("/register", json=user_json)
        return response

    @patch(f"{resource_path}.register")
    def test_registration_user(self, mock_register):
        with self.app_context():
            response = self.send_register_request()
            self.assertEqual(response.status_code, 201)
            expected_message = "Succesfully created user."
            self.assertEqual(response.get_json()['message'], expected_message)

        mock_register.assert_called_once_with(
            self.username, self.email, self.password, False
        )

    @patch(f"{resource_path}.register")
    def test_registration_admin_user_correct(self, mock_register):
        self.app.config['ADMIN_KEY'] = 'correct_key'

        with self.app_context():
            response = self.send_register_request(key='correct_key')
            self.assertEqual(response.status_code, 201)
            expected_message = "Succesfully created user."
            self.assertEqual(response.get_json()['message'], expected_message)

        mock_register.assert_called_once_with(
            self.username, self.email, self.password, True
        )

    @patch(f"{resource_path}.register")
    def test_registration_admin_user_incorrect(self, mock_register):
        self.app.config['ADMIN_KEY'] = 'correct_key'

        with self.app_context():
            response = self.send_register_request(key='incorrect_key')
            self.assertEqual(response.status_code, 403)
            expected_message = "Incorrect admin key."
            self.assertEqual(response.get_json()['message'], expected_message)

        mock_register.assert_not_called()

    @patch(
        f"{resource_path}.get_identity",
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
