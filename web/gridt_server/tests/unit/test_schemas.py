from marshmallow import ValidationError

from gridt_server.tests.base_test import BaseTest
from gridt_server.schemas import (
    MovementSchema,
    NewUserSchema,
    RequestEmailChangeSchema,
    ChangeEmailSchema,
)

from freezegun import freeze_time
from unittest.mock import patch

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
        # test that e-mail or username missing gives
        # appropriate error
        pass

    def test_request_email_change_schema_email_invalid(self):
        # test that invalid e-mail will give appropriate error
        pass

    def test_request_email_change_schema_correct(self):
        with self.app_context():
            proper_request = {
                "password": "password",
                "new_email": "proper@email.com",
            }

            # Make sure no error is thrown with this info
            res = schema.load(proper_request)
            self.assertEqual(res, proper_request)

    def test_change_email_schema_token_expired(self):
        with self.app_context():
            # patch jwt validation to give ExpiredSignatureError
            # side effect

            schema = ChangeEmailSchema()
            with self.assertRaises(ValidationError) as error:
                schema.load(bad_request)

                self.assertEqual(
                    error.exception.messages, {"token": ["Signature has expired."]}
                )

    def test_change_email_schema_token_invalid(self):
        with self.app_context():
            # patch jwt validation to give InvalidTokenError
            # side effect

            schema = ChangeEmailSchema()
            with self.assertRaises(ValidationError) as error:
                schema.load(bad_request)

                self.assertEqual(
                    error.exception.messages, {"token": ["Invalid token."]}
                )

    def test_change_email_schema_correct(self):
        with self.app_context():
            # proper_request = {"token": "foo"}
            # patch jwt validation to not throw an error

            # Make sure no error is thrown with this info
            schema = ChangeEmailSchema()
            res = schema.load(proper_request)
            self.assertEqual(res, proper_request)