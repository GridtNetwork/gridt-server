import sys
import base64
import logging
from tests.base_test import BaseTest
from models.user import User
from auth.auth import auth
from flask import current_app

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer


class AuthTest(BaseTest):
    def test_verify(self):
        with self.app_context():
            stream_handler = logging.StreamHandler(sys.stdout)
            self.logger.addHandler(stream_handler)
            user = User("username", "password")
            user.save_to_db()

            @self.app.route("/test")
            @auth.login_required
            def test_route():
                return ""

            self.assertEqual(self.client.get("/test").status_code, 401)
            creds = base64.b64encode(b"username:password").decode("utf-8")
            self.assertEqual(
                self.client.get(
                    "/test", headers={"Authorization": "Basic " + creds}
                ).status_code,
                200,
            )

    def test_auth_token(self):
        with self.app_context():
            user = User("username", "password")
            user.save_to_db()

            token = user.generate_auth_token()

            self.assertIsNotNone(token)
            s = Serializer(current_app.config["SECRET_KEY"])
            self.assertEqual(s.loads(token), {"id": user.id})

            self.assertTrue(user.verify_auth_token(token))
