from marshmallow import ValidationError

from gridt.tests.base_test import BaseTest
from gridt.schemas import MovementSchema, NewUserSchema


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
            self.assertEqual(res, proper_movement)

    def test_movement_schema_missing_data(self):
        """
        Check that a movement following a bad schema will give an error
        if one of the required fields is missing.
        """
        with self.app_context():
            bad_movement = {}

            schema = MovementSchema()
            with self.assertRaises(ValidationError) as error:
                schema.load(bad_movement)
            self.assertEqual(
                error.exception.messages,
                {
                    "name": ["Missing data for required field."],
                    "short_description": ["Missing data for required field."],
                    "interval": ["Missing data for required field."],
                },
            )

    def test_movement_schema_lengths(self):
        with self.app_context():
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

    def test_movement_schema_existing(self):
        with self.app_context():
            movement = self.create_movement()
        
            bad_movement = {
                "name": self.movements[0].name,
                "short_description": "This is a new movement",
                "interval": "daily",
            }

            schema = MovementSchema()
            with self.assertRaises(ValidationError) as error:
                schema.load(bad_movement)
            
            self.assertEqual(
                error.exception.messages,
                {
                    "name": ["Could not create movement, because movement name is already in use."],
                },
            )

