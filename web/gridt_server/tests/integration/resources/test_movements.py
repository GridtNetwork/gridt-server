import json
from freezegun import freeze_time
from unittest.mock import patch
from datetime import datetime

from gridt_server.tests.base_test import BaseTest
from gridt_server.db import db
from gridt_server.models import User, Movement, Signal


class MovementsTest(BaseTest):
    def test_get_movements(self):
        with self.app_context():
            user = User("test1", "test1@test.com", "pass")
            user2 = User("test2", "test2@test.com", "pass")
            movement1 = Movement("test1", "twice daily", "Hello")
            movement2 = Movement("test2", "daily", "Hello")
            movement3 = Movement("test3", "weekly", "Testing")
            db.session.add_all([user, user2, movement1, movement2, movement3])
            db.session.commit()

            movement1.add_user(user)
            signal = Signal(user, movement1)
            signal2 = Signal(user, movement1)
            db.session.add_all([signal, signal2])
            db.session.commit()

            movement1.add_user(user2)
            movement2.add_user(user)

            movement3.add_user(user)
            movement3.add_user(user2)
            signal3 = Signal(user, movement3, "test message")
            db.session.add(signal3)
            db.session.commit()

            # To prevent sqlalchemy.orm.exc.DetachedInstanceError
            stamp2 = str(signal2.time_stamp.astimezone())
            stamp3 = str(signal3.time_stamp.astimezone())

            token = self.obtain_token("test2@test.com", "pass")

            # Check that the response matches expectation
            resp = self.client.get(
                "/movements", headers={"Authorization": f"JWT {token}"}
            )

            expected = [
                {
                    "id": 1,
                    "description": "",
                    "interval": "twice daily",
                    "last_signal_sent": None,
                    "leaders": [
                        {
                            "id": 1,
                            "last_signal": {"time_stamp": stamp2},
                            "username": "test1",
                            "bio": "",
                            "avatar": user.get_email_hash(),
                        }
                    ],
                    "name": "test1",
                    "short_description": "Hello",
                    "subscribed": True,
                },
                {
                    "id": 2,
                    "description": "",
                    "interval": "daily",
                    "name": "test2",
                    "short_description": "Hello",
                    "subscribed": False,
                },
                {
                    "id": 3,
                    "description": "",
                    "interval": "weekly",
                    "name": "test3",
                    "short_description": "Testing",
                    "subscribed": True,
                    "last_signal_sent": None,
                    "leaders": [
                        {
                            "id": 1,
                            "last_signal": {
                                "time_stamp": stamp3,
                                "message": "test message",
                            },
                            "username": "test1",
                            "bio": "",
                            "avatar": user.get_email_hash(),
                        }
                    ],
                },
            ]
            self.assertEqual(resp.get_json(), expected)

    def test_post_name_exists(self):
        with self.app_context():
            movement = Movement("move", "daily")
            movement.save_to_db()
            user = User("test1", "test@test.com", "pass")
            user.save_to_db()

            token = self.obtain_token("test@test.com", "pass")

            movement_dict = {
                "name": "move",
                "short_description": "Hi, hello this is a test",
                "interval": "weekly",
            }
            resp = self.client.post(
                "/movements",
                headers={"Authorization": f"JWT {token}"},
                json=movement_dict,
            )

            self.assertEqual(
                json.loads(resp.data),
                {"message": "name: Movement name already in use."},
            )
            self.assertEqual(resp.status_code, 400)

    def test_interval_empty(self):
        with self.app_context():
            user = User("test1", "test1@test.com", "pass")
            user.save_to_db()

            token = self.obtain_token("test1@test.com", "pass")

            movement_dict = {
                "name": "movement",
                "short_description": "Hi, this is a test",
                "interval": "",
            }

            resp = self.client.post(
                "/movements",
                headers={"Authorization": f"JWT {token}"},
                json=movement_dict,
            )

            self.assertEqual(
                json.loads(resp.data),
                {
                    "message": (
                        "interval: Must be one of: " "daily, twice daily, weekly."
                    )
                },
            )
            self.assertEqual(resp.status_code, 400)

    def test_invalid_movement(self):
        with self.app_context():
            user = User("test1", "test@test.com", "pass")
            user.save_to_db()

            token = self.obtain_token("test@test.com", "pass")

            movement_dict = {
                "name": "movement",
                "short_description": "Hi, this is a test",
            }

            resp = self.client.post(
                "/movements",
                headers={"Authorization": f"JWT {token}"},
                json=movement_dict,
            )

            self.assertEqual(
                json.loads(resp.data),
                {"message": "interval: Missing data for required field."},
            )
            self.assertEqual(resp.status_code, 400)

    def test_name_empty(self):
        with self.app_context():
            user = User("test1", "test@test.com", "pass")
            user.save_to_db()

            token = self.obtain_token("test@test.com", "pass")

            movement_dict = {
                "name": "",
                "short_description": "Hi, hello this is a test",
                "interval": "daily",
            }

            resp = self.client.post(
                "/movements",
                headers={"Authorization": f"JWT {token}"},
                json=movement_dict,
            )

            self.assertEqual(
                json.loads(resp.data),
                {"message": "name: Length must be between 4 and 50."},
            )
            self.assertEqual(resp.status_code, 400)

    def test_post_successful(self):
        with self.app_context():
            user = self.create_user()

            movement_dict = {
                "name": "movement",
                "short_description": "Hi, hello this is a test",
                "interval": "daily",
            }

            resp = self.request_as_user(
                self.users[0], "POST", "/movements", json=movement_dict,
            )

            self.assertEqual(
                json.loads(resp.data), {"message": "Successfully created movement."},
            )
            self.assertEqual(resp.status_code, 201)

            movement = Movement.find_by_name("movement")
            self.assertIsNotNone(movement)
            self.assertEqual(movement.interval, "daily")
            self.assertEqual(movement.short_description, "Hi, hello this is a test")
            self.assertEqual(len(movement.current_users), 1)
            self.assertEqual(movement.current_users[0], user)

    def test_single_movement_by_name(self):
        with self.app_context():
            user = User("test1", "test@test.com", "pass")
            user.save_to_db()
            movement = Movement("1", "daily", "Hello")
            movement.save_to_db()

            token = self.obtain_token("test@test.com", "pass")

            resp1 = self.client.get(
                "/movements/1", headers={"Authorization": f"JWT {token}"},
            )
            resp2 = self.client.get(
                "/movements/1", headers={"Authorization": f"JWT {token}"}
            )
            expected = {
                "id": 1,
                "name": "1",
                "short_description": "Hello",
                "description": "",
                "interval": "daily",
                "subscribed": False,
            }
            self.assertEqual(json.loads(resp1.data), expected)
            self.assertEqual(json.loads(resp2.data), expected)
            self.assertEqual(resp1.status_code, 200)
            self.assertEqual(resp2.status_code, 200)

    def test_single_movement_non_existing(self):
        with self.app_context():
            user = User("test1", "test@test.com", "pass")
            user.save_to_db()

            token = self.obtain_token("test@test.com", "pass")

            resp1 = self.client.get(
                "/movements/1", headers={"Authorization": f"JWT {token}"},
            )
            resp2 = self.client.get(
                "/movements/1", headers={"Authorization": f"JWT {token}"}
            )

            self.assertEqual(resp1.status_code, 400)
            self.assertEqual(resp2.status_code, 400)

            self.assertEqual(
                json.loads(resp1.data),
                {"message": "movement_id: No movement found for that id."},
            )
            self.assertEqual(
                json.loads(resp2.data),
                {"message": "movement_id: No movement found for that id."},
            )


class SubscribeTest(BaseTest):
    def test_subscribe(self):
        with self.app_context():
            user = User("test1", "test@test.com", "pass")
            user.save_to_db()
            movement = Movement("1", "daily", "Hello")
            movement.save_to_db()

            token = self.obtain_token("test@test.com", "pass")

            resp = self.client.put(
                "/movements/1/subscriber", headers={"Authorization": f"JWT {token}"},
            )

        # Using self.client will call db.session.commit(), this will close the
        # current session. We will have to create a new one and load the
        # movement and the user again.
        with self.app_context():
            user = User.find_by_id(1)
            movement = Movement.find_by_id(1)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(
                json.loads(resp.data),
                {"message": "Successfully subscribed to this movement."},
            )

            self.assertTrue(user in movement.current_users)
            self.assertTrue(movement in user.current_movements)

            # Do it twice, should not change anything.
            resp = self.client.put(
                "/movements/1/subscriber", headers={"Authorization": f"JWT {token}"},
            )
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(
                json.loads(resp.data),
                {"message": "Successfully subscribed to this movement."},
            )

            self.assertTrue(user in movement.current_users)
            self.assertTrue(movement in user.current_movements)

    def test_subscribe_non_existing(self):
        with self.app_context():
            user = User("test1", "test@test.com", "pass")
            user.save_to_db()

            token = self.obtain_token("test@test.com", "pass")

            resp = self.client.put(
                "/movements/1/subscriber", headers={"Authorization": f"JWT {token}"},
            )
            self.assertEqual(resp.status_code, 400)
            self.assertEqual(
                resp.get_json(),
                {"message": "movement_id: No movement found for that id."},
            )

    def test_unsubscribe(self):
        with self.app_context():
            movement = self.create_movement()
            user = self.create_user_in_movement(movement)

            resp = self.request_as_user(
                self.users[0], "DELETE", f"/movements/{movement.id}/subscriber",
            )

            self.assertEqual(resp.status_code, 200)
            self.assertEqual(
                json.loads(resp.data),
                {"message": "Successfully unsubscribed from this movement."},
            )

            user = User.find_by_id(1)
            movement = Movement.find_by_id(1)

            self.assertNotIn(user, movement.current_users)
            self.assertNotIn(movement, user.current_movements)

        # Using self.client will call db.session.commit(), this will close the
        # current session. We will have to create a new one and load the
        # movement and the user again.
        with self.app_context():
            # Do it twice, should not change anything.
            resp = self.request_as_user(
                self.users[0], "DELETE", f"/movements/{movement.id}/subscriber",
            )

            self.assertEqual(resp.status_code, 200)
            self.assertEqual(
                json.loads(resp.data),
                {"message": "Successfully unsubscribed from this movement."},
            )

            self.assertTrue(user not in movement.current_users)
            self.assertTrue(movement not in user.current_movements)

    def test_unsubscribe_non_existing(self):
        with self.app_context():
            user = User("test1", "test@test.com", "pass")
            user.save_to_db()

            token = self.obtain_token("test@test.com", "pass")

            resp = self.client.delete(
                "/movements/1/subscriber", headers={"Authorization": f"JWT {token}"},
            )
            self.assertEqual(resp.status_code, 404)
            self.assertEqual(
                json.loads(resp.data),
                {"message": "movement_id: No movement found for that id."},
            )


class NewSignalTest(BaseTest):
    def test_create_new_signal(self):
        with self.app_context(), freeze_time("1996-03-15"):
            movement = Movement("1", "daily", "Hi")
            movement.save_to_db()
            user = User("test1", "test@test.com", "pass")
            user.save_to_db()

            movement.add_user(user)

            token = self.obtain_token("test@test.com", "pass")

            resp = self.client.post(
                "/movements/1/signal", headers={"Authorization": f"JWT {token}"},
            )

            self.assertEqual(
                json.loads(resp.data), {"message": "Successfully created signal."},
            )
            self.assertEqual(resp.status_code, 201)

        with self.app_context():
            user = User.find_by_id(1)
            movement = Movement.find_by_id(1)
            self.assertEqual(
                Signal.find_last(user, movement).time_stamp, datetime(1996, 3, 15),
            )

    def test_movement_nonexistant(self):
        with self.app_context():
            user = User("test1", "test@test.com", "pass")
            user.save_to_db()

            token = self.obtain_token("test@test.com", "pass")

            resp = self.client.post(
                "/movements/1/signal", headers={"Authorization": f"JWT {token}"},
            )

            self.assertEqual(resp.status_code, 400)
            self.assertEqual(
                json.loads(resp.data),
                {"message": "movement_id: No movement found for that id."},
            )

    def test_movement_not_subscribed(self):
        with self.app_context():
            movement = Movement("1", "daily")
            movement.save_to_db()
            user = User("test1", "test@test.com", "pass")
            user.save_to_db()

            token = self.obtain_token("test@test.com", "pass")

            resp = self.client.post(
                "/movements/1/signal", headers={"Authorization": f"JWT {token}"},
            )

            self.assertEqual(resp.status_code, 400)
            self.assertEqual(
                json.loads(resp.data),
                {"message": "_schema: User not subscribed to movement"},
            )


class SubscriptionsResourceTest(BaseTest):
    def test_get_subscriptions(self):
        with self.app_context():
            self.create_movement()
            self.create_movement()

            now = "1995-01-15 12:00:00+01:00"
            later = "1996-03-15 11:00:00+01:00"

            self.create_user_in_movement(self.movements[0])
            with freeze_time(now, tz_offset=1):
                self.signal_as_user(self.users[0], self.movements[0])
            with freeze_time(later, tz_offset=1):
                self.signal_as_user(self.users[0], self.movements[0])

            self.create_user_in_movement(self.movements[0])
            self.movements[1].add_user(self.get_user(0))

            self.assertTrue(self.movements[1] not in self.get_user(1).movements)

            resp = self.request_as_user(
                self.users[1], "GET", "/movements/subscriptions"
            )

            user_dict = self.users[0]
            del user_dict["password"]
            del user_dict["email"]
            user_dict["last_signal"] = {"time_stamp": later}

            expected = [
                {
                    "id": 1,
                    "name": self.movements[0].name,
                    "interval": self.movements[0].interval,
                    "short_description": self.movements[0].short_description,
                    "description": self.movements[0].description,
                    "subscribed": True,
                    "last_signal_sent": None,
                    "leaders": [user_dict],
                }
            ]
            data = json.loads(resp.data)
            self.maxDiff = None
            self.assertEqual(data, expected)

    def test_unsubscribe_get_subscriptions(self):
        with self.app_context():
            self.create_movement()
            self.create_user_in_movement(self.movements[0])

            resp_delete = self.request_as_user(
                self.users[0], "DELETE", "/movements/1/subscriber"
            )

            self.assertEqual(resp_delete.status_code, 200)

            resp = self.request_as_user(
                self.users[0], "GET", "/movements/subscriptions"
            )
            data = json.loads(resp.data)

            self.assertEqual(resp.status_code, 200)
            self.assertEqual(data, [])
