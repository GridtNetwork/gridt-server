from datetime import datetime, timedelta
from unittest.mock import patch

from gridt.db import db
from gridt.tests.base_test import BaseTest
from gridt.models.signal import Signal
from gridt.models.user import User
from gridt.models.movement import Movement

NOW = datetime.now()
LATER = datetime.now() + timedelta(hours=10)


class SignalTest(BaseTest):
    @patch("gridt.models.signal.Signal._get_now", side_effect=[NOW, LATER])
    def test_crud(self, now):
        with self.app_context():
            user = User("username", "test@test.com", "password")
            user.save_to_db()
            movement = Movement("flossing", "daily")
            movement.save_to_db()

            self.assertIsNone(Signal.find_last(user, movement))

            signal1 = Signal(user, movement)
            signal1.save_to_db()
            self.assertEqual(Signal.find_last(user, movement), signal1)

            self.assertEqual(signal1.movement, movement)
            self.assertEqual(signal1.leader, user)
            self.assertEqual(signal1.message, None)
            self.assertEqual(signal1.time_stamp, NOW)

            signal2 = Signal(user, movement, "test message")
            signal2.save_to_db()
            self.assertEqual(Signal.find_last(user, movement), signal2)

            self.assertEqual(signal2.movement, movement)
            self.assertEqual(signal2.leader, user)
            self.assertEqual(signal2.message, "test message")
            self.assertEqual(signal2.time_stamp, LATER)

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
