from gridt.tests.base_test import BaseTest
from gridt.models.updates import Update
from gridt.models.user import User
from gridt.models.movement import Movement


class UpdateTest(BaseTest):
    def test_create(self):
        user = User("username", "password")
        movement = Movement("flossing")

        update = Update(user, movement)

        self.assertEqual(update.leader, user)
        self.assertEqual(update.movement, movement)
