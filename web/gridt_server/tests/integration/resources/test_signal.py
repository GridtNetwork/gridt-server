from freezegun import freeze_time
from unittest.mock import patch

from gridt_server.tests.base_test import BaseTest
from gridt_server.db import db
from src.models.user import User
from src.models.movement import Movement
from src.models.signal import Signal


class SignalTest(BaseTest):
    @patch("flask_jwt_extended.view_decorators.verify_jwt_in_request")
    def test_send_signal(self, verify_func):
        """
        In the database "now" a signal by user1 in movement1 is stored.
        It is then checked that user2 can see this. Then at "later" user1
        sends a request to create a signal with a message. User2 requests
        this message.
        """
        with self.app_context():
            now = "1995-01-15 12:00:00+01:00"
            later = "1996-03-15 12:00:00+01:00"

            user1 = User("test1", "test1@test.com", "pass")
            user2 = User("test2", "test2@test.com", "pass")
            movement1 = Movement("test movement 1", "twice daily", "Hello")
            db.session.add_all([user1, user2, movement1])
            db.session.commit()

            movement1.add_user(user1)
            movement1.add_user(user2)
            with freeze_time(now, tz_offset=1):
                signal = Signal(user1, movement1)
                db.session.add_all([signal])
                db.session.commit()

            with patch(
                "gridt_server.resources.movements.get_jwt_identity", return_value=2,
            ):
                resp1 = self.client.get("/movements/1")

            expected1 = {"time_stamp": now}
            self.assertEqual(resp1.get_json()["leaders"][0]["last_signal"], expected1)

            with freeze_time(later, tz_offset=1), patch(
                "gridt_server.resources.movements.get_jwt_identity", return_value=1,
            ):
                self.client.post(
                    "/movements/1/signal", json={"message": "Test Message"},
                )

            with patch(
                "gridt_server.resources.movements.get_jwt_identity", return_value=2,
            ):
                resp2 = self.client.get("/movements/1")

            expected2 = {"time_stamp": later, "message": "Test Message"}
            self.assertEqual(resp2.get_json()["leaders"][0]["last_signal"], expected2)
