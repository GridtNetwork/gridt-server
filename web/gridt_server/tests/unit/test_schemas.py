from marshmallow import ValidationError

from gridt_server.tests.base_test import BaseTest
from gridt_server.schemas import (
    MovementSchema,
    RequestEmailChangeSchema,
    ChangeEmailSchema,
)

from freezegun import freeze_time

class SchemasTest(BaseTest):
    def test_movement_schema_long(self):
        with self.app_context():
            proper_movement = {
                "name": "flossing",
                "short_description": "Flossing everyday keeps the dentist away.",
                "description": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Vivamus eget sapien ipsum. Nulla eget felis id mi maximus vestibulum a ac lorem. Ut eget arcu sed urna pellentesque hendrerit eu eget ipsum. Sed congue scelerisque dapibus. Suspendisse neque mi, vehicula vel malesuada at, pretium non sapien. Phasellus mi ex, congue.",
                "interval": "daily",
            }

            # Make sure no error is thrown with this info
            schema = MovementSchema()
            res = schema.load(proper_movement)
            self.assertEqual(res, proper_movement)

    def test_movement_schema_short(self):
        with self.app_context():
            proper_movement = {
                "name": "flossing",
                "short_description": "Flossing sometimes is good for you.",
                "interval": "weekly",
            }

            # Make sure no error is thrown with this info
            schema = MovementSchema()
            res = schema.load(proper_movement)
            self.assertEqual(res["name"], "flossing")

    def test_movement_schema_bad_interval(self):
        with self.app_context():
            bad_movement = {"name": "flossing", "interval": "daily"}

            schema = MovementSchema()
            with self.assertRaises(ValidationError) as error:
                schema.load(bad_movement)

                self.assertEqual(
                    error.exception.messages,
                    {"short_description": ["Missing data for required field."],},
                )

    def test_movement_schema_lengths(self):
        bad_movement = {
            "name": "flo",
            "short_description": "1234567",
            "interval": "daily",
        }

        schema = MovementSchema()
        with self.assertRaises(ValidationError) as error:
            schema.load(bad_movement)

            self.assertEqual(
                error.exception.messages,
                {
                    "short_description": ["Length must be between 10 and 100."],
                    "name": ["Length must be between 4 and 50."],
                },
            )

    def test_request_email_change_schema_invalid(self):
        with self.app_context():
            user = self.create_user()
            bad_request = {
                "password": "bad_password",
                "new_email": "bad_email",
            }
            schema = RequestEmailChangeSchema()
            schema.context = {"user": user}
            with self.assertRaises(ValidationError) as error:
                schema.load(bad_request)

                self.assertEqual(
                    error.exception.messages,
                    {
                        "password": ["Failed to identify user with given password."],
                        "new_email": ["Not a valid email address."],
                    },
                )

    def test_request_email_change_schema_correct(self):
        with self.app_context():
            user = self.create_user()
            proper_request = {
                "password": self.users[0]["password"],
                "new_email": "proper@email.com",
            }
            schema = RequestEmailChangeSchema()
            schema.context = {"user": user}

            # Make sure no error is thrown with this info
            res = schema.load(proper_request)
            self.assertEqual(res, proper_request)

    def test_change_email_schema_token_expired(self):
        with self.app_context():
            user = self.create_user()
            new_email = "new@email.com"
            with freeze_time("2020-04-18 22:10:00"):
                token = user.get_email_change_token(new_email)
            with freeze_time("2020-04-19 00:10:01"):
                bad_request = {"token": token}

                schema = ChangeEmailSchema()
                with self.assertRaises(ValidationError) as error:
                    schema.load(bad_request)

                    self.assertEqual(
                        error.exception.messages, {"token": ["Signature has expired."]}
                    )

    def test_change_email_schema_token_invalid(self):
        with self.app_context():
            bad_request = {
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
                "eyJpZCI6MSwiZXhwIjoxNTg3MzM0MjAwfW."
                "2qdnq1_YJS9tgKVlIVpBbaAanyxQnCyVmV6s7QcOuBo",
            }

            schema = ChangeEmailSchema()
            with self.assertRaises(ValidationError) as error:
                schema.load(bad_request)

                self.assertEqual(
                    error.exception.messages, {"token": ["Invalid token."]}
                )

    def test_change_email_schema_correct(self):
        with self.app_context():
            user = self.create_user()
            new_email = "new@email.com"
            token = user.get_email_change_token(new_email)
            proper_request = {"token": token}

            # Make sure no error is thrown with this info
            schema = ChangeEmailSchema()
            res = schema.load(proper_request)
            self.assertEqual(res, proper_request)
