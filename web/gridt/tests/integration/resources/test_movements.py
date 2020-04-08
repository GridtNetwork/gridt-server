import json
from unittest.mock import patch
from datetime import datetime

from gridt.tests.base_test import BaseTest
from gridt.db import db
from gridt.models.user import User
from gridt.models.movement import Movement
from gridt.models.movement import Signal


class MovementsTest(BaseTest):
    def test_get_movements(self):
        with self.app_context():
            # Create fake data
            user = User("test1", "test1@test.com", "pass")
            user2 = User("test2", "test2@test.com", "pass")
            movement = Movement("test", "twice daily", "Hello")
            movement2 = Movement("test", "daily", "Hello")
            db.session.add_all([user, user2, movement, movement2])
            db.session.commit()

            movement.add_user(user)
            signal = Signal(user, movement)
            signal2 = Signal(user, movement)
            db.session.add_all([signal, signal2])
            db.session.commit()

            movement.add_user(user2)
            movement2.add_user(user)

            # To prevent sqlalchemy.orm.exc.DetachedInstanceError
            stamp = str(signal2.time_stamp.astimezone())

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
                    "leaders": [{"id": 1, "last_signal": stamp, "username": "test1"}],
                    "name": "test",
                    "short_description": "Hello",
                    "subscribed": True,
                },
                {
                    "id": 2,
                    "description": "",
                    "interval": "daily",
                    "name": "test",
                    "short_description": "Hello",
                    "subscribed": False,
                },
            ]

            self.assertEqual(json.loads(resp.data), expected)

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

    def test_post_sucessful(self):
        with self.app_context():
            user = User("test1", "test@test.com", "pass")
            user.save_to_db()

            token = self.obtain_token("test@test.com", "pass")

            movement_dict = {
                "name": "movement",
                "short_description": "Hi, hello this is a test",
                "interval": "daily",
            }

            resp = self.client.post(
                "/movements",
                headers={"Authorization": f"JWT {token}"},
                json=movement_dict,
            )

            self.assertEqual(
                json.loads(resp.data), {"message": "Successfully created movement."}
            )
            self.assertEqual(resp.status_code, 201)

            movement = Movement.find_by_name("movement")
            self.assertIsNotNone(movement)
            self.assertEqual(movement.interval, "daily")
            self.assertEqual(movement.short_description, "Hi, hello this is a test")

    def test_single_movement_by_name(self):
        with self.app_context():
            user = User("test1", "test@test.com", "pass")
            user.save_to_db()
            movement = Movement("Flossing", "daily", "Hello")
            movement.save_to_db()

            token = self.obtain_token("test@test.com", "pass")

            resp1 = self.client.get(
                "/movements/Flossing", headers={"Authorization": f"JWT {token}"}
            )
            resp2 = self.client.get(
                "/movements/1", headers={"Authorization": f"JWT {token}"}
            )
            expected = {
                "id": 1,
                "name": "Flossing",
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
                "/movements/Flossing", headers={"Authorization": f"JWT {token}"}
            )
            resp2 = self.client.get(
                "/movements/1", headers={"Authorization": f"JWT {token}"}
            )

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
            user = User("test1", "test@test.com", "pass")
            user.save_to_db()
            movement = Movement("Flossing", "daily", "Hello")
            movement.save_to_db()

            token = self.obtain_token("test@test.com", "pass")

            resp = self.client.put(
                "/movements/Flossing/subscriber",
                headers={"Authorization": f"JWT {token}"},
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

            self.assertTrue(user in movement.users)
            self.assertTrue(movement in user.movements)

            # Do it twice, should not change anything.
            resp = self.client.put(
                "/movements/Flossing/subscriber",
                headers={"Authorization": f"JWT {token}"},
            )
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(
                json.loads(resp.data),
                {"message": "Successfully subscribed to this movement."},
            )

            self.assertTrue(user in movement.users)
            self.assertTrue(movement in user.movements)

    def test_subscribe_non_existing(self):
        with self.app_context():
            user = User("test1", "test@test.com", "pass")
            user.save_to_db()

            token = self.obtain_token("test@test.com", "pass")

            resp = self.client.put(
                "/movements/Flossing/subscriber",
                headers={"Authorization": f"JWT {token}"},
            )
            self.assertEqual(resp.status_code, 404)
            self.assertEqual(
                json.loads(resp.data), {"message": "This movement does not exist."}
            )

    def test_unsubscribe(self):
        with self.app_context():
            user = User("test1", "test@test.com", "pass")
            user.save_to_db()
            movement = Movement("Flossing", "daily", "Hello")
            movement.save_to_db()
            movement.add_user(user)

            # To prevent sqlalchemy.orm.exc.DetachedInstanceError
            users = movement.users
            movements = user.movements

            token = self.obtain_token("test@test.com", "pass")

            resp = self.client.delete(
                "/movements/Flossing/subscriber",
                headers={"Authorization": f"JWT {token}"},
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
                {"message": "Successfully unsubscribed from this movement."},
            )

            self.assertTrue(not user in movement.users)
            self.assertTrue(not movement in user.movements)

            # Do it twice, should not change anything.
            resp = self.client.delete(
                "/movements/Flossing/subscriber",
                headers={"Authorization": f"JWT {token}"},
            )

            self.assertEqual(resp.status_code, 200)
            self.assertEqual(
                json.loads(resp.data),
                {"message": "Successfully unsubscribed from this movement."},
            )

        with self.app_context():
            user = User.find_by_id(1)
            movement = Movement.find_by_id(1)

            self.assertTrue(not user in movement.users)
            self.assertTrue(not movement in user.movements)

    def test_unsubscribe_non_existing(self):
        with self.app_context():
            user = User("test1", "test@test.com", "pass")
            user.save_to_db()

            token = self.obtain_token("test@test.com", "pass")

            resp = self.client.delete(
                "/movements/Flossing/subscriber",
                headers={"Authorization": f"JWT {token}"},
            )
            self.assertEqual(resp.status_code, 404)
            self.assertEqual(
                json.loads(resp.data), {"message": "This movement does not exist."}
            )


class SwapTest(BaseTest):
    def test_swap_leader(self):
        with self.app_context():
            movement = Movement("Flossing", "daily", "Hi")

            user1 = User("test1", "test1@test.com", "pass")
            user2 = User("test2", "test2@test.com", "pass")
            user3 = User("test3", "test3@test.com", "pass")
            user4 = User("test4", "test4@test.com", "pass")
            user5 = User("test5", "test5@test.com", "pass")

            signal = Signal(user3, movement)
            time_stamp = signal.time_stamp

            db.session.add_all([user1, user2, user2, user2, user2, signal, movement])

            movement.add_user(user1)
            movement.add_user(user2)
            movement.add_user(user3)
            movement.add_user(user4)
            movement.add_user(user5)

            token = self.obtain_token("test1@test.com", "pass")

            resp = self.client.post(
                "/movements/Flossing/leader/5",
                headers={"Authorization": f"JWT {token}"},
            )

    def test_swap_leader_movement_nonexistant(self):
        with self.app_context():
            user1 = User("test", "test1@test.com", "pass")
            user1.save_to_db()

            token = self.obtain_token("test1@test.com", "pass")

            resp = self.client.post(
                "/movements/Flossing/leader/2",
                headers={"Authorization": f"JWT {token}"},
            )

            self.assertEqual(resp.status_code, 404)
            self.assertEqual(
                json.loads(resp.data), {"message": "This movement does not exist."}
            )

    def test_swap_leader_movement_not_subscribed(self):
        with self.app_context():
            movement = Movement("Flossing", "daily", "Hi")
            movement.save_to_db()
            user1 = User("test1", "test1@test.com", "pass")
            user1.save_to_db()

            token = self.obtain_token("test1@test.com", "pass")

            resp = self.client.post(
                "/movements/Flossing/leader/1",
                headers={"Authorization": f"JWT {token}"},
            )

            self.assertEqual(resp.status_code, 400)
            self.assertEqual(
                json.loads(resp.data),
                {"message": "User is not subscribed to this movement."},
            )

    def test_swap_leader_not_leader(self):
        with self.app_context():
            movement = Movement("Flossing", "daily", "Hi")
            movement.save_to_db()
            user1 = User("test1", "test1@test.com", "pass")
            user1.save_to_db()
            user2 = User("test2", "test2@test.com", "pass")
            user2.save_to_db()
            movement.add_user(user1)

            token = self.obtain_token("test1@test.com", "pass")

            resp = self.client.post(
                "/movements/Flossing/leader/2",
                headers={"Authorization": f"JWT {token}"},
            )

            self.assertEqual(resp.status_code, 400)
            self.assertEqual(
                json.loads(resp.data), {"message": "User is not following this leader."}
            )


class NewSignalTest(BaseTest):
    @patch("gridt.models.signal.Signal._get_now", return_value=datetime(1996, 3, 15))
    def test_create_new_signal(self, func):
        with self.app_context():
            movement = Movement("Flossing", "daily", "Hi")
            movement.save_to_db()
            user = User("test1", "test@test.com", "pass")
            user.save_to_db()

            movement.add_user(user)

            token = self.obtain_token("test@test.com", "pass")

            resp = self.client.post(
                "/movements/Flossing/signal", headers={"Authorization": f"JWT {token}"}
            )

            self.assertEqual(
                json.loads(resp.data), {"message": "Successfully created signal."}
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
            user = User("test1", "test@test.com", "pass")
            user.save_to_db()

            token = self.obtain_token("test@test.com", "pass")

            resp = self.client.post(
                "/movements/Flossing/signal", headers={"Authorization": f"JWT {token}"}
            )

            self.assertEqual(resp.status_code, 404)
            self.assertEqual(
                json.loads(resp.data), {"message": "This movement does not exist."}
            )

    def test_movement_not_subscribed(self):
        with self.app_context():
            movement = Movement("Flossing", "daily")
            movement.save_to_db()
            user = User("test1", "test@test.com", "pass")
            user.save_to_db()

            token = self.obtain_token("test@test.com", "pass")

            resp = self.client.post(
                "/movements/Flossing/signal", headers={"Authorization": f"JWT {token}"}
            )

            self.assertEqual(resp.status_code, 400)
            self.assertEqual(
                json.loads(resp.data),
                {"message": "User is not subscribed to this movement."},
            )


class SubscriptionsResourceTest(BaseTest):
    def test_get_subscriptions(self):
        with self.app_context():
            # Create fake data
            user = User("test1", "test1@test.com", "pass")
            user2 = User("test2", "test2@test.com", "pass")
            movement = Movement("movement1", "twice daily", "Hello")
            movement2 = Movement("movement2", "daily", "Hello")
            db.session.add_all([user, user2, movement, movement2])
            db.session.commit()

            # User test1 subscribes to movement1 and does an signal
            movement.add_user(user)
            signal = Signal(user, movement)
            signal2 = Signal(user, movement)
            db.session.add_all([signal, signal2])
            db.session.commit()

            # User test2 subscribes to movement1 and test1 to movement2
            movement.add_user(user2)
            movement2.add_user(user)

            self.assertTrue(movement2 not in user2.movements)
            # To prevent sqlalchemy.orm.exc.DetachedInstanceError
            stamp = str(signal2.time_stamp.astimezone())

            token = self.obtain_token("test2@test.com", "pass")

            # Check that the response matches expectation
            resp = self.client.get(
                "/movements/subscriptions", headers={"Authorization": f"JWT {token}"}
            )

            expected = [
                {
                    "id": 1,
                    "description": "",
                    "interval": "twice daily",
                    "last_signal_sent": None,
                    "leaders": [{"id": 1, "last_signal": stamp, "username": "test1"}],
                    "name": "movement1",
                    "short_description": "Hello",
                    "subscribed": True,
                }
            ]
            data = json.loads(resp.data)
            self.assertEqual(data, expected)
