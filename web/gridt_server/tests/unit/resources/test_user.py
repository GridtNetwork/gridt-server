from unittest import skip
from unittest.mock import patch
import datetime
import jwt

from gridt_server.tests.base_test import BaseTest


class UserResourceTest(BaseTest):
    user_id = 42
    password = old_password = "my_password"
    new_password = "my_secr3t"
    not_password = "wrong_password"
    email = old_email = "any@email.com"
    new_email = "new@email.com"
    not_email = "not@email.com"

    def send_bio_request(self, body, user_id):
        response = self.client.put(
            "/bio",
            headers={"Authorization": self.obtain_token_header(user_id)},
            json=body
        )
        return response

    @patch("gridt_server.resources.user.update_user_bio")
    def test_update_bio(self, mock_update_bio):
        body = {"bio": "new_bio"}

        with self.app_context():
            response = self.send_bio_request(body, self.user_id)
            self.assertEqual(response.status_code, 200)
            expected = {"message": "Bio successfully changed."}
            self.assertEqual(response.get_json(), expected)

        mock_update_bio.assert_called_once_with(self.user_id, body["bio"])

    @patch("gridt_server.resources.user.update_user_bio")
    def test_update_bio_improperly(self, mock_update_bio):
        body = {}

        with self.app_context():
            response = self.send_bio_request(body, self.user_id)
            self.assertEqual(response.status_code, 400)
            expected = {"message": "bio: Missing data for required field."}
            self.assertEqual(response.get_json(), expected)

        mock_update_bio.assert_not_called()

    def send_change_password_request(self, body, user_id):
        response = self.client.post(
            "/user/change_password",
            headers={"Authorization": self.obtain_token_header(user_id)},
            json=body
        )
        return response

    @patch("gridt_server.schemas.verify_password_for_id", return_value=1)
    @patch("gridt_server.resources.user.change_password")
    def test_change_password_with_no_password(
        self, mock_change_passwod, mock_verify_password
    ):
        body1 = {}
        expect_messsage_1 = "new_password: Missing data for required field."
        body2 = {"old_password": self.old_password}
        expect_messsage_2 = "new_password: Missing data for required field."

        with self.app_context():
            response1 = self.send_change_password_request(body1, self.user_id)
            mock_verify_password.assert_not_called()
            response2 = self.send_change_password_request(body2, self.user_id)

        self.assertEqual(response1.status_code, 400)
        self.assertEqual(response2.status_code, 400)
        self.assertEqual(response2.get_json()["message"], expect_messsage_1)
        self.assertEqual(response2.get_json()["message"], expect_messsage_2)

        mock_verify_password.assert_called()
        mock_change_passwod.assert_not_called()

    @patch("gridt_server.schemas.verify_password_for_id", return_value=0)
    @patch("gridt_server.resources.user.change_password")
    def test_change_password_with_wrong_password(
        self, mock_change_passwod, mock_verify_password
    ):
        incorrect = "wrong_password"
        body = {
            "old_password": incorrect,
            "new_password": self.new_password
        }
        expect_message = "old_password: " \
            "Failed to identify user with given password."

        with self.app_context():
            response = self.send_change_password_request(body, self.user_id)
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.get_json()["message"], expect_message)

        mock_verify_password.assert_called_with(self.user_id, incorrect)
        mock_change_passwod.assert_not_called()

    @patch("gridt_server.schemas.verify_password_for_id", return_value=1)
    @patch("gridt_server.resources.user.change_password")
    def test_change_password_with_correct_password(
        self, mock_change, mock_verify
    ):
        body = {
            "old_password": self.old_password,
            "new_password": self.new_password
        }
        expect_message = "Successfully changed password."

        with self.app_context():
            response = self.send_change_password_request(body, self.user_id)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json()["message"], expect_message)

        mock_verify.assert_called_with(self.user_id, self.old_password)
        mock_change.assert_called_with(self.user_id, self.new_password)

    def test_no_api_key(self):
        """
        Don't ask me what this test is testing
        """
        with self.app_context():
            self.app.config["EMAIL_API_KEY"] = None

            resp = self.client.post(
                "/user/reset_password/request", json={"email": self.email},
            )

            self.assertIn("message", resp.get_json())
            self.assertEqual(resp.status_code, 500)

    def send_reset_email_request(self, body, user_id):
        response = self.client.post(
            "/user/change_email/request",
            headers={"Authorization": self.obtain_token_header(user_id)},
            json=body
        )
        return response

    @patch("gridt_server.resources.user.request_email_change")
    @patch("gridt_server.schemas.verify_password_for_id", return_value=1)
    def test_send_password_reset_email_correct(
        self, mock_request_email_change, mock_verify_password
    ):
        body = {"new_email": self.email, "password": self.old_password}

        with self.app_context():
            response = self.send_reset_email_request(body, self.user_id)

            # In order to not give away sensitive information
            # message must be the same as a successful attempt
            self.assertIn("message", response.get_json())
            self.assertEqual(response.status_code, 200)

        mock_request_email_change.assert_called()
        mock_verify_password.assert_called_with(
            self.user_id, self.email, self.app.config["SECRET_KEY"]
        )

    def send_reset_password_token_request(self, token, password=new_password):
        response = self.client.post(
            "/user/reset_password/confirm",
            json={"token": token, "password": password}
        )
        return response

    def get_password_token(self, user_id, secret_key, expire_in=2):
        expires = datetime.datetime.now() + datetime.timedelta(hours=expire_in)
        expires = expires.timestamp()

        payload = {"user_id": user_id, "exp": expires}
        return jwt.encode(payload, secret_key, algorithm="HS256")

    @patch("gridt_server.resources.user.reset_password")
    def test_reset_password_token_correct(self, mock_reset):
        with self.app_context():
            secret_key = self.app.config["SECRET_KEY"]
            token = self.get_password_token(self.user_id, secret_key)
            response = self.send_reset_password_token_request(token)

            self.assertIn("message", response.get_json())
            self.assertEqual(response.status_code, 200)

        mock_reset.assert_called_with(
            token=token, password=self.new_password, secret_key=secret_key
        )

    @patch("gridt_server.resources.user.reset_password")
    def test_reset_password_token_expired(self, mock_reset):
        with self.app_context():
            secret_key = self.app.config["SECRET_KEY"]
            token_expired = self.get_password_token(
                self.user_id, secret_key, expire_in=-1
            )
            response = self.send_reset_password_token_request(token_expired)

            self.assertIn("message", response.get_json())
            self.assertEqual(response.status_code, 400)

        mock_reset.assert_not_called()

    @patch("gridt_server.resources.user.reset_password")
    def test_password_reset_token_tampered(self, mock_reset):
        tampered_token = (
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
            "eyJpZCI6MSwiZXhwIjoxNTg3MzM0MjAwfW."
            "2qdnq1_YJS9tgKVlIVpBbaAanyxQnCyVmV6s7QcOuBo"
        )

        with self.app_context():
            response = self.send_reset_password_token_request(tampered_token)

            self.assertIn("message", response.get_json())
            self.assertEqual(response.status_code, 400)

        mock_reset.assert_not_called()

    def send_email_change_request(self, body, user_id):
        response = self.client.post(
            "/user/change_email/request",
            headers={"Authorization": self.obtain_token_header(user_id)},
            json=body
        )
        return response

    @patch("gridt_server.resources.user.request_email_change")
    @patch("gridt_server.schemas.verify_password_for_id", return_value=1)
    def test_request_email_change_correct(
        self, mock_verify_password, mock_request_email_change
    ):
        body = {
            "password": self.password, "new_email": self.new_email
        }
        expected_message = "Successfully sent verification e-mail." \
            " Check your inbox."

        with self.app_context():
            response = self.send_email_change_request(body, self.user_id)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json()['message'], expected_message)

        mock_verify_password.assert_called_with(self.user_id, self.password)
        mock_request_email_change.assert_called_with(
            self.user_id, self.new_email, self.app.config["SECRET_KEY"]
        )

    @patch("gridt_server.resources.user.request_email_change")
    @patch("gridt_server.schemas.verify_password_for_id", return_value=0)
    def test_request_email_change_bad_schema(
        self, mock_verify_password, mock_request_email_change
    ):
        body = {"new_email": self.new_email}
        expected_message = "password: Missing data for required field."

        with self.app_context():
            response = self.send_email_change_request(body, self.user_id)

            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.get_json()['message'], expected_message)

        mock_verify_password.assert_not_called()
        mock_request_email_change.assert_not_called()

    def send_change_email_token_request(self, token):
        response = self.client.post(
            "/user/change_email/confirm",
            json={"token": token}
        )
        return response

    def get_email_token(self, user_id, new_email, secret_key, expire_in=2):
        expires = datetime.datetime.now() + datetime.timedelta(hours=expire_in)
        expires = expires.timestamp()

        payload = {"user_id": user_id, "new_email": new_email, "exp": expires}
        return jwt.encode(payload, secret_key, algorithm="HS256")

    @skip("This test is broken because the get_jwt_identity() without token")
    @patch("gridt_server.resources.user.change_email")
    def test_change_email_change_existing_email(self, mock_change):
        with self.app_context():
            secret_key = self.app.config["SECRET_KEY"]
            token = self.get_email_token(
                self.user_id, self.new_email, secret_key
            )
            response = self.send_change_email_token_request(token)

            self.assertIn("message", response.get_json())
            self.assertEqual(response.status_code, 200)

        mock_change.assert_called_with(self.user_id, token, secret_key)

    @patch("gridt_server.resources.user.change_email")
    def test_change_email_change_bad_schema(self, mock_change):
        with self.app_context():
            response = self.client.post("/user/change_email/confirm", json={})
            self.assertEqual(response.status_code, 400)

        mock_change.assert_not_called()
