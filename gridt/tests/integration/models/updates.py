from tests.base_test import BaseTest
from models.updates import Update
from models.user import User
from models.movement import Movement

class UpdateTest(BaseTest):
    def test_create(self):
        user = User('username', 'password')
        movement = Movement('flossing')

        update = Update(user, movement)

        self.assertEqual(update.leader, user)
        self.assertEqual(update.movement, movement)

