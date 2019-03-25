import json
from datetime import timedelta

from gridt.tests.base_test import BaseTest
from gridt.db import db
from gridt.models.user import User
from gridt.models.movement import Movement
from gridt.models.movement import Update


class MovementsTest(BaseTest):
    def test_get(self):
        with self.app_context():
            # Create fake data
            user = User("test1", "test@test.com", "pass")
            user2 = User("test2", "test@test.com", "pass")
            movement = Movement("test", timedelta(hours=2), "Hello")
            movement2 = Movement("test", timedelta(days=2), "Hello")
            db.session.add_all([user, user2, movement, movement2])
            db.session.commit()

            movement.add_user(user)
            update = Update(user, movement)
            update2 = Update(user, movement)
            db.session.add_all([update, update2])
            db.session.commit()

            movement.add_user(user2)
            movement2.add_user(user)

            # To prevent sqlalchemy.orm.exc.DetachedInstanceError
            stamp = str(update2.time_stamp)

            token = self.obtain_token("test2", "pass")

            # Check that the response matches expectation
            resp = self.client.get(
                "/movements", headers={"Authorization": f"JWT {token}"}
            )

            expected = [
                {
                    "id": 1,
                    "description": "",
                    "interval": {"days": 0, "hours": 2},
                    "leaders": [{"id": 1, "last-update": stamp, "username": "test1"}],
                    "name": "test",
                    "short_description": "Hello",
                    "subscribed": True,
                },
                {
                    "id": 2,
                    "description": "",
                    "interval": {"days": 2, "hours": 0},
                    "name": "test",
                    "short_description": "Hello",
                    "subscribed": False,
                },
            ]

            self.assertEqual(json.loads(resp.data), expected)

    def test_post_name_exists(self):
        with self.app_context():
            movement = Movement("move", timedelta(days=1))
            movement.save_to_db()
            user = User("test1", "test@test.com", "pass")
            user.save_to_db()

            token = self.obtain_token("test1", "pass")

            movement_dict = {
                "name": "move",
                "short_description": "Hi, hello this is a test",
                "interval": {"days": 3, "hours": 0},
            }
            resp = self.client.post(
                "/movements",
                headers={"Authorization": f"JWT {token}"},
                json=movement_dict,
            )

            self.assertEqual(
                json.loads(resp.data),
                {"message": "Could not create movement, because it already exists."},
            )
            self.assertEqual(resp.status_code, 400)

    def test_interval_empty(self):
        with self.app_context():
            user = User("test1", "test@test.com", "pass")
            user.save_to_db()

            token = self.obtain_token("test1", "pass")

            movement_dict = {
                "name": "movement",
                "short_description": "Hi, this is a test",
                "interval": {"days": 0, "hours": 0},
            }

            resp = self.client.post(
                "/movements",
                headers={"Authorization": f"JWT {token}"},
                json=movement_dict,
            )

            self.assertEqual(
                json.loads(resp.data), {"message": "Interval must be nonzero."}
            )
            self.assertEqual(resp.status_code, 400)

    def test_name_empty(self):
        with self.app_context():
            user = User("test1", "test@test.com", "pass")
            user.save_to_db()

            token = self.obtain_token("test1", "pass")

            movement_dict = {
                "name": "",
                "short_description": "Hi, hello this is a test",
                "interval": {"days": 1, "hours": 0},
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

            token = self.obtain_token("test1", "pass")

            movement_dict = {
                "name": "movement",
                "short_description": "Hi, hello this is a test",
                "interval": {"days": 3, "hours": 0},
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
            self.assertEqual(movement.interval, timedelta(days=3))
            self.assertEqual(movement.short_description, "Hi, hello this is a test")

    def test_single_movement_by_name(self):
        with self.app_context():
            user = User("test1", "test@test.com", "pass")
            user.save_to_db()
            movement = Movement("Flossing", timedelta(days=2), "Hello")
            movement.save_to_db()

            token = self.obtain_token("test1", "pass")

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
                "interval": {"days": 2, "hours": 0},
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

            token = self.obtain_token("test1", "pass")

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

    def test_subscribe(self):
        with self.app_context():
            user = User("test1", "test@test.com", "pass")
            user.save_to_db()
            movement = Movement("Flossing", timedelta(days=2), "Hello")
            movement.save_to_db()

            token = self.obtain_token("test1", "pass")

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

            token = self.obtain_token("test1", "pass")

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
            movement = Movement("Flossing", timedelta(days=2), "Hello")
            movement.save_to_db()
            movement.add_user(user)

            # To prevent sqlalchemy.orm.exc.DetachedInstanceError
            users = movement.users
            movements = user.movements

            token = self.obtain_token("test1", "pass")

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

            token = self.obtain_token("test1", "pass")

            resp = self.client.delete(
                "/movements/Flossing/subscriber",
                headers={"Authorization": f"JWT {token}"},
            )
            self.assertEqual(resp.status_code, 404)
            self.assertEqual(
                json.loads(resp.data), {"message": "This movement does not exist."}
            )
