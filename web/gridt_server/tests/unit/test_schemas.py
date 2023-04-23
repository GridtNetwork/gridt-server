from marshmallow import ValidationError

from gridt_server.tests.base_test import BaseTest
from gridt_server.schemas import (
    MovementSchema,
    RequestEmailChangeSchema,
    ChangeEmailSchema,
)

from unittest.mock import patch

import jwt


class SchemasTest(BaseTest):
    @patch("gridt_server.schemas.movement_name_exists", return_value=False)
    def test_movement_schema_long(self, mock_name_exists):
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
            mock_name_exists.assert_called_once_with("flossing")

    @patch("gridt_server.schemas.movement_name_exists", return_value=False)
    def test_movement_schema_short2(self, mock_name_exists):
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
            mock_name_exists.assert_called_once_with("flossing")

    @patch("gridt_server.schemas.movement_name_exists", return_value=False)
    def test_movement_schema_bad_interval(self, mock_name_exists):
        with self.app_context():
            bad_movement = {"name": "flossing", "interval": "daily"}

            schema = MovementSchema()
            with self.assertRaises(ValidationError) as error:
                schema.load(bad_movement)

                self.assertEqual(
                    error.exception.messages,
                    {"short_description": ["Missing data for required field."],},
                )
            mock_name_exists.assert_called_once_with("flossing")

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

    @patch(
        "gridt_server.schemas.verify_password_for_id",
        return_value=False
    )
    def test_request_email_change_schema_invalid(self, mock_verify_password):
        with self.app_context(), self.assertRaises(ValidationError) as error:
            bad_request = {
                "password": "bad_password",
                "new_email": "bad_email",
            }

            schema = RequestEmailChangeSchema()
            schema.context["user_id"] = 42

            schema.load(bad_request)

        self.assertEqual(
            error.exception.messages["password"],
            ["Failed to identify user with given password."]
        )
        self.assertEqual(
            error.exception.messages["new_email"],
            ["Not a valid email address."]
        )
        mock_verify_password.assert_called_once_with(42, "bad_password")

    @patch(
        "gridt_server.schemas.verify_password_for_id",
        return_value=True
    )
    def test_request_email_change_schema_correct(self, mock_verify_password):
        with self.app_context():
            proper_request = {
                "password": "correct",
                "new_email": "proper@email.com",
            }
            schema = RequestEmailChangeSchema()

            schema.context["user_id"] = 42

            # Make sure no error is thrown with this info
            res = schema.load(proper_request)
            self.assertEqual(res, proper_request)
            mock_verify_password.assert_called_once_with(42, "correct")

    @patch(
        "gridt_server.schemas.jwt.decode",
        side_effect=jwt.ExpiredSignatureError()
    )
    def test_change_email_schema_token_expired(self, mock_jwt_decode):
        with self.app_context(), self.assertRaises(ValidationError) as error:
            bad_request = {"token": "expired token"}
            self.app.config["SECRET_KEY"] = "secr3t"

            schema = ChangeEmailSchema()
            schema.load(bad_request)

        self.assertEqual(
            error.exception.messages, {"token": ["Signature has expired."]}
        )

        mock_jwt_decode.assert_called_once_with(
            "expired token",
            "secr3t",
            algorithms=["HS256"]
        )

    @patch(
        "gridt_server.schemas.jwt.decode",
        side_effect=jwt.InvalidTokenError()
    )
    def test_change_email_schema_token_invalid(self, mock_jwt_decode):
        with self.app_context(), self.assertRaises(ValidationError) as error:
            bad_request = {"token": "bad token"}
            self.app.config["SECRET_KEY"] = "secr3t"

            schema = ChangeEmailSchema()

            schema.load(bad_request)

        self.assertEqual(
            error.exception.messages, {"token": ["Invalid token."]}
        )

        mock_jwt_decode.assert_called_once_with(
            "bad token",
            "secr3t",
            algorithms=["HS256"]
        )

    @patch(
        "gridt_server.schemas.jwt.decode",
        side_effect=None
    )
    def test_change_email_schema_correct(self, mock_jwt_decode):
        with self.app_context():
            proper_request = {"token": "some token"}
            self.app.config["SECRET_KEY"] = "secr3t"

            schema = ChangeEmailSchema()
            res = schema.load(proper_request)
            self.assertEqual(res, proper_request)

        mock_jwt_decode.assert_called_once_with(
            "some token",
            "secr3t",
            algorithms=["HS256"]
        )
