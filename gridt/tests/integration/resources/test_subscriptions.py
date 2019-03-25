import json
from datetime import timedelta

from gridt.tests.base_test import BaseTest
from gridt.db import db
from gridt.models.user import User
from gridt.models.movement import Movement
from gridt.models.movement import Update


class SubscriptionsResourceTest(BaseTest):
    def test_get(self):
        with self.app_context():
            # Create fake data
            user = User("test1", "test@test.com", "pass")
            user2 = User("test2", "test@test.com", "pass")
            movement = Movement("movement1", timedelta(hours=2), "Hello")
            movement2 = Movement("movement2", timedelta(days=2), "Hello")
            db.session.add_all([user, user2, movement, movement2])
            db.session.commit()

            # User test1 subscribes to movement1 and does an update
            movement.add_user(user)
            update = Update(user, movement)
            update2 = Update(user, movement)
            db.session.add_all([update, update2])
            db.session.commit()

            # User test2 subscribes to movement1 and test1 to movement2
            movement.add_user(user2)
            movement2.add_user(user)

            self.assertTrue(movement2 not in user2.movements)
            # To prevent sqlalchemy.orm.exc.DetachedInstanceError
            stamp = str(update2.time_stamp)

            token = self.obtain_token("test2", "pass")

            # Check that the response matches expectation
            resp = self.client.get(
                "/movements/subscriptions", headers={"Authorization": f"JWT {token}"}
            )

            expected = [
                {
                    "description": "",
                    "interval": {"days": 0, "hours": 2},
                    "leaders": [{"id": 1, "last-update": stamp, "username": "test1"}],
                    "name": "movement1",
                    "short_description": "Hello",
                    "subscribed": True,
                }
            ]
            data = json.loads(resp.data)
            self.assertEqual(data, expected)
