from marshmallow import ValidationError

from gridt.tests.base_test import BaseTest
from gridt.schemas import MovementSchema, NewUserSchema


class SchemasTest(BaseTest):
    def test_movement_schema_long(self):
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
