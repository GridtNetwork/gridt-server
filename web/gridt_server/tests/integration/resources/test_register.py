import json
from gridt_server.tests.base_test import BaseTest


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
            # check that gridt.controllers.user.register is called with stuff in user_json

    def test_logged_in(self):
        with self.app_context():
            # check that gridt.controllers.user.get_identity is called with flask_jwt_extended.get_jwt_identity
            # (remember to import from flask_jwt_extended)
            pass
