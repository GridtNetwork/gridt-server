from datetime import timedelta, datetime
from unittest.mock import patch

from gridt.db import db
from gridt.tests.base_test import BaseTest
from gridt.models.update import Update
from gridt.models.user import User
from gridt.models.movement import Movement


class UpdateTest(BaseTest):
    @patch("gridt.models.update.Update._get_now", return_value=datetime.now())
    def test_crud(self, now):
        with self.app_context():
            user = User("username", "test@test.com", "password")
            user.save_to_db()
            movement = Movement("flossing", timedelta(days=2))
            movement.save_to_db()

            self.assertIsNone(Update.find_last(user, movement))
            update = Update(user, movement)
            update.save_to_db()

            self.assertEqual(Update.find_last(user, movement), update)

    def test_find_last(self):
        with self.app_context():
            user = User("username", "test@test.com", "password")
            user.save_to_db()
            movement = Movement("flossing", timedelta(days=2))
            movement.save_to_db()
            update = Update(user, movement)
            update.save_to_db()

            update2 = Update(user, movement)
            update2.save_to_db()
