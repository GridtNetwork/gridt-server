import json
import lorem
from unittest.mock import patch
from datetime import datetime

from gridt.tests.base_test import BaseTest
from gridt.db import db
from gridt.models import User, Movement, Signal, MovementUserAssociation


class MovementsTest(BaseTest):
    def test_get_movements(self):
        """
        movement1:
            user1 (signal1, signal2) <-> user2
        movement2:
            user1
        movement3:
            user1 <-> user2
            (signal3)
        """
        with self.app_context():
            movement1 = self.create_movement()
            movement2 = self.create_movement()
            movement3 = self.create_movement()
            user1 = self.create_user_in_movement(movement1)

            signal1 = self.signal_as_user(self.users[0], self.movements[0])
            signal2 = self.signal_as_user(self.users[0], self.movements[0])

            user2 = self.create_user_in_movement(movement1)

            movement2.add_user(user1)

            movement3.add_user(user1)
            movement3.add_user(user2)
            signal3 = self.signal_as_user(
                self.users[0], movement3, message="test message"
            )

            # To prevent sqlalchemy.orm.exc.DetachedInstanceError
            stamp2 = str(signal2.time_stamp.astimezone())
            stamp3 = str(signal3.time_stamp.astimezone())

            # Check that the response matches expectation
            resp = self.request_as_user(self.users[1], "GET", "/movements",)

            expected = [
                {
                    "id": 1,
                    "description": movement1.description,
                    "interval": movement1.interval,
                    "name": movement1.name,
                    "short_description": movement1.short_description,
                    "subscribed": True,
                    "last_signal_sent": None,
                    "leaders": [
                        {
                            "id": 1,
                            "last_signal": {"time_stamp": stamp2},
                            "username": self.users[0]["username"],
                            "bio": "",
                            "avatar": self.users[0]["avatar"],
                        }
                    ],
                },
                {
                    "id": 2,
                    "description": movement2.description,
                    "interval": movement2.interval,
                    "name": movement2.name,
                    "short_description": movement2.short_description,
                    "subscribed": False,
                },
                {
                    "id": 3,
                    "description": movement3.description,
                    "interval": movement3.interval,
                    "name": movement3.name,
                    "short_description": movement3.short_description,
                    "subscribed": True,
                    "last_signal_sent": None,
                    "leaders": [
                        {
                            "id": 1,
                            "last_signal": {
                                "time_stamp": stamp3,
                                "message": "test message",
                            },
                            "username": self.users[0]["username"],
                            "bio": "",
                            "avatar": self.users[0]["avatar"],
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
                {
                    "message": "Could not create movement, because movement name is already in use."
                },
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
                {"message": "interval: Must be one of: daily, twice daily, weekly."},
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
                json.loads(resp.data), {"message": "Successfully created movement."}
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
            user = self.create_user()
            movement = self.create_movement()

            resp1 = self.request_as_user(
                self.users[0], "GET", f"/movements/{movement.name}",
            )
            resp2 = self.request_as_user(self.users[0], "GET", "/movements/1",)
            expected = {
                "id": 1,
                "name": movement.name,
                "short_description": movement.short_description,
                "description": movement.description,
                "interval": movement.interval,
                "subscribed": False,
            }
            self.assertEqual(json.loads(resp1.data), expected)
            self.assertEqual(json.loads(resp2.data), expected)
            self.assertEqual(resp1.status_code, 200)
            self.assertEqual(resp2.status_code, 200)

    def test_single_movement_non_existing(self):
        with self.app_context():
            user = self.create_user()

            resp1 = self.request_as_user(self.users[0], "GET", "/movements/Flossing",)
            resp2 = self.request_as_user(self.users[0], "GET", "/movements/1",)

            self.assertEqual(resp1.status_code, 404)
            self.assertEqual(resp2.status_code, 404)

            self.assertEqual(
                json.loads(resp1.data), {"message": "This movement does not exist."}
            )
            self.assertEqual(
                json.loads(resp2.data), {"message": "This movement does not exist."}
            )


class SubscribeTest(BaseTest):
    def test_subscribe(self):
        with self.app_context():
            movement = self.create_movement()
            user = self.create_user()

            resp = self.request_as_user(
                self.users[0], "PUT", "/movements/1/subscriber",
            )

        # Using self.client will call db.session.commit(), this will close the
        # current session. We will have to create a new one and load the
        # movement and the user again.
        with self.app_context():
            user = User.find_by_id(1)
            movement = Movement.find_by_id(1)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(
                resp.get_json(),
                {"message": "Successfully subscribed to this movement."},
            )

            self.assertTrue(user in movement.current_users)
            self.assertTrue(movement in user.current_movements)

            # Do it twice, should not change anything.
            resp = self.request_as_user(
                self.users[0], "PUT", "/movements/1/subscriber",
            )
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(
                resp.get_json(),
                {"message": "Successfully subscribed to this movement."},
            )

            self.assertTrue(user in movement.current_users)
            self.assertTrue(movement in user.current_movements)

    def test_subscribe_non_existing(self):
        with self.app_context():
            user = self.create_user()

            resp = self.request_as_user(
                self.users[0], "PUT", "/movements/Flossing/subscriber",
            )
            self.assertEqual(resp.status_code, 404)
            self.assertEqual(
                resp.get_json(), {"message": "This movement does not exist."}
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
                resp.get_json(),
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
                resp.get_json(),
                {"message": "Successfully unsubscribed from this movement."},
            )

            self.assertTrue(not user in movement.current_users)
            self.assertTrue(not movement in user.current_movements)

    def test_unsubscribe_non_existing(self):
        with self.app_context():
            user = self.create_user()

            resp = self.request_as_user(
                self.users[0], "DELETE", "/movements/Flossing/subscriber",
            )
            self.assertEqual(resp.status_code, 404)
            self.assertEqual(
                resp.get_json(), {"message": "This movement does not exist."}
            )


class NewSignalTest(BaseTest):
    @patch("gridt.models.signal.Signal._get_now", return_value=datetime(1996, 3, 15))
    def test_create_new_signal(self, func):
        with self.app_context():
            movement = self.create_movement()
            user = self.create_user_in_movement(movement)

            resp = self.request_as_user(
                self.users[0], "POST", f"/movements/{movement.name}/signal",
            )

            self.assertEqual(
                resp.get_json(), {"message": "Successfully created signal."}
            )
            self.assertEqual(resp.status_code, 201)

        with self.app_context():
            user = User.find_by_id(1)
            movement = Movement.find_by_id(1)
            self.assertEqual(
                Signal.find_last(user, movement).time_stamp, datetime(1996, 3, 15)
            )

    def test_movement_nonexistant(self):
        with self.app_context():
            user = self.create_user()

            resp = self.request_as_user(
                self.users[0], "POST", "/movements/Flossing/signal",
            )

            self.assertEqual(resp.status_code, 404)
            self.assertEqual(
                resp.get_json(), {"message": "This movement does not exist."}
            )

    def test_movement_not_subscribed(self):
        with self.app_context():
            movement = self.create_movement()
            user = self.create_user()

            resp = self.request_as_user(self.users[0], "POST", "/movements/1/signal",)

            self.assertEqual(resp.status_code, 400)
            self.assertEqual(
                resp.get_json(),
                {"message": "User is not subscribed to this movement."},
            )


class SubscriptionsResourceTest(BaseTest):
    def test_get_subscriptions(self):
        with self.app_context():
            self.create_movement()
            self.create_movement()

            now = datetime(1995, 1, 15, 8)
            later = datetime(1996, 3, 15, 11)

            self.create_user_in_movement(self.movements[0])
            self.signal_as_user(self.users[0], self.movements[0], moment=now)
            self.signal_as_user(self.users[0], self.movements[0], moment=later)

            self.create_user_in_movement(self.movements[0])
            self.movements[1].add_user(self.get_user(0))

            self.assertTrue(self.movements[1] not in self.get_user(1).movements)

            resp = self.request_as_user(
                self.users[1], "GET", "/movements/subscriptions"
            )

            user_dict = self.users[0]
            del user_dict["password"]
            del user_dict["email"]
            user_dict["last_signal"] = {"time_stamp": str(later.astimezone())}

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
