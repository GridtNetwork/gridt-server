from tests.base_test import BaseTest
from models.movement import Movement

class MovementTest(BaseTest):
    def test_create(self):
        movement = Movement('flossing')
        self.assertEqual(movement.name, 'flossing')
        self.assertIsNone(movement.short_description)
        self.assertIsNone(movement.description)

        movement2 = Movement('toothpicking', 'pick your teeth every day!')
        self.assertEqual(movement2.name, 'toothpicking')
        self.assertEqual(movement2.short_description, 'pick your teeth every day!')
