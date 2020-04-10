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
            user1 = User("test1", "test1@test.com", "pass")
            user2 = User("test2", "test2@test.com", "pass")
            movement1 = Movement("test movement 1", "twice daily", "Hello")
            db.session.add_all([user1, user2, movement1])
            db.session.commit()

            movement1.add_user(user1)
            movement1.add_user(user2)
            signal = Signal(user1, movement1)
            db.session.add_all([signal])
            db.session.commit()

            token1 = self.obtain_token("test1@test.com", "pass")
            token2 = self.obtain_token("test2@test.com", "pass")

            resp1 = self.client.get(
                "/movements/1", headers={"Authorization": f"JWT {token2}"}
            )

            expected1 = {"time_stamp": str(NOW.astimezone())}
            self.assertEqual(
                json.loads(resp1.data)["leaders"][0]["last_signal"], expected1
            )

            self.client.post(
                "/movements/1/signal",
                data=json.dumps({"message": "Hello"}),
                content_type="application/json",
                headers={"Authorization": f"JWT {token1}"},
            )

            resp2 = self.client.get(
                "/movements/1", headers={"Authorization": f"JWT {token2}"}
            )

            expected2 = {"time_stamp": str(LATER.astimezone()), "message": "Hello"}
            self.assertEqual(
                json.loads(resp2.data)["leaders"][0]["last_signal"], expected2
            )
