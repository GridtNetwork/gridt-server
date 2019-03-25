from marshmallow import ValidationError

from gridt.tests.base_test import BaseTest
from gridt.schemas import MovementSchema, IntervalSchema


class SchemasTest(BaseTest):
    def test_movement_schema_long(self):
        proper_movement = {
            "name": "flossing",
            "short_description": "Flossing everyday keeps the dentist away.",
            "long-description": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Vivamus eget sapien ipsum. Nulla eget felis id mi maximus vestibulum a ac lorem. Ut eget arcu sed urna pellentesque hendrerit eu eget ipsum. Sed congue scelerisque dapibus. Suspendisse neque mi, vehicula vel malesuada at, pretium non sapien. Phasellus mi ex, congue.",
            "interval": {"hours": 1, "days": 10},
        }

        # Make sure no error is thrown with this info
        schema = MovementSchema()
        res = schema.load(proper_movement)

    def test_movement_schema_short(self):
        proper_movement = {
            "name": "flossing",
            "short_description": "Flossing sometimes is good for you.",
            "interval": {"hours": 1, "days": 10},
        }

        # Make sure no error is thrown with this info
        schema = MovementSchema()
        res = schema.load(proper_movement)
        self.assertEqual(res.data["name"], "flossing")
        self.assertEqual(res.errors, {})

    def test_movement_schema_bad_interval(self):
        bad_movement = {"name": "flossing", "interval": {"days": 0, "hours": 0}}

        schema = MovementSchema()
        res = schema.load(bad_movement)
        self.assertEqual(
            res.errors,
            {
                "interval": {"_schema": ["Interval must be nonzero."]},
                "short_description": ["Missing data for required field."],
            },
        )

    def test_movement_schema_lengths(self):
        bad_movement = {
            "name": "flo",
            "short_description": "1234567",
            "interval": {"days": 1, "hours": 0},
        }

        schema = MovementSchema()
        res = schema.load(bad_movement)
        print(res.errors)

    def test_interval_schema(self):
        good_interval = {"days": 0, "hours": 1}

        bad_interval = {"days": 0, "hours": 0}

        schema = IntervalSchema()
        schema.load(good_interval)
        res = schema.load(bad_interval)
        self.assertEqual(res.errors, {"_schema": ["Interval must be nonzero."]})
