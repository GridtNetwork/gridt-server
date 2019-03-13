from datetime import timedelta

from gridt.tests.base_test import BaseTest
from gridt.models.updates import Update
from gridt.models.user import User
from gridt.models.movement import Movement


class UpdateTest(BaseTest):
    def test_create(self):
        user = User("username", "test@test.com", "password")
        movement = Movement("flossing", timedelta(days=2))

        update = Update(user, movement)

        self.assertEqual(update.leader, user)
        self.assertEqual(update.movement, movement)
