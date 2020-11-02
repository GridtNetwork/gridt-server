import lorem
from freezegun import freeze_time
from datetime import datetime, timedelta
from unittest.mock import patch

from gridt_server.tests.base_test import BaseTest
from gridt_server.models.signal import Signal
from gridt_server.models.user import User
from gridt_server.models.movement import Movement

NOW = datetime.now()
LATER = datetime.now() + timedelta(hours=10)


class SignalTest(BaseTest):
    @patch("gridt_server.models.signal.Signal._get_now", side_effect=[NOW, LATER])
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

    def test_get_signal_history(self):
        with self.app_context():
            movement = self.create_movement()
            user = self.create_user_in_movement(movement)

            dates = [
                "2001-1-2",
                "2017-9-15",
                "2019-10-18",
                "2020-9-2",
            ]

            signals = []
            for date in dates:
                with freeze_time(date):
                    signal = self.signal_as_user(
                        self.users[0], movement, message=lorem.sentence(),
                    )
                    signals.append(signal)

            expected = list(reversed(signals[-2:]))

            self.assertEqual(Signal.get_signal_history(user, movement, 2), expected)
