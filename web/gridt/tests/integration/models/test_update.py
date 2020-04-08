from datetime import datetime
from unittest.mock import patch

from gridt.db import db
from gridt.tests.base_test import BaseTest
from gridt.models.signal import Signal
from gridt.models.user import User
from gridt.models.movement import Movement


class SignalTest(BaseTest):
    @patch("gridt.models.signal.Signal._get_now", return_value=datetime.now())
    def test_crud(self, now):
        with self.app_context():
            user = User("username", "test@test.com", "password")
            user.save_to_db()
            movement = Movement("flossing", "daily")
            movement.save_to_db()

            self.assertIsNone(Signal.find_last(user, movement))
            signal = Signal(user, movement)
            signal.save_to_db()

            self.assertEqual(Signal.find_last(user, movement), signal)

    def test_find_last(self):
        with self.app_context():
            user = User("username", "test@test.com", "password")
            user.save_to_db()
            movement = Movement("flossing", "daily")
            movement.save_to_db()
            signal = Signal(user, movement)
            signal.save_to_db()

            signal2 = Signal(user, movement)
            signal2.save_to_db()
