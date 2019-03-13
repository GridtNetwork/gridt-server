from datetime import timedelta
from gridt.tests.base_test import BaseTest
from gridt.models.movement import Movement


class MovementTest(BaseTest):
    def test_create(self):
        movement = Movement("flossing", timedelta(days=2))

        self.assertEqual(movement.name, "flossing")
        self.assertEqual(movement.interval.days, 2)
        self.assertIsNone(movement.short_description)
        self.assertIsNone(movement.description)

        movement2 = Movement(
            "toothpicking", timedelta(days=1), "pick your teeth every day!"
        )

        self.assertEqual(movement2.name, "toothpicking")
        self.assertEqual(movement2.interval.days, 1)
        self.assertEqual(movement2.short_description, "pick your teeth every day!")
        self.assertIsNone(movement.description)
