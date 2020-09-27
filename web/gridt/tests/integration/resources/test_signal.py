import json
from unittest.mock import patch
from datetime import datetime, timedelta

from gridt.tests.base_test import BaseTest
from gridt.db import db
from gridt.models.user import User
from gridt.models.movement import Movement
from gridt.models.movement import Signal

NOW = datetime.now()
LATER = datetime.now() + timedelta(hours=10)


class SignalTest(BaseTest):
    @patch("gridt.models.signal.Signal._get_now", side_effect=[NOW, LATER])
    def test_send_signal(self, get_now_mock):
        with self.app_context():
            # Create fake data
            movement = self.create_movement()
            user1 = self.create_user_in_movement(movement)
            user2 = self.create_user_in_movement(movement)

            signal = self.signal_as_user(self.users[0], movement)

            resp1 = self.request_as_user(
                self.users[1],
                "GET",
                "/movements/1",
            )

            expected1 = {"time_stamp": str(NOW.astimezone())}
            self.assertEqual(resp1.get_json()["leaders"][0]["last_signal"], expected1)

            self.request_as_user(
                self.users[0],
                "POST",
                "/movements/1/signal",
                json={"message": "Hello"},
            )

            resp2 = self.request_as_user(
                self.users[1],
                "GET",
                "/movements/1",
            )

            expected2 = {"time_stamp": str(LATER.astimezone()), "message": "Hello"}
            self.assertEqual(resp2.get_json()["leaders"][0]["last_signal"], expected2)
