from datetime import timedelta, datetime
from unittest.mock import patch

from gridt.tests.base_test import BaseTest
from gridt.db import db
from gridt.models.movement import Movement
from gridt.models.user import User
from gridt.models.update import Update


class MovementTest(BaseTest):
    def test_create(self):
        movement = Movement("flossing", timedelta(days=2))

        self.assertEqual(movement.name, "flossing")
        self.assertEqual(movement.interval.days, 2)
        self.assertEqual(movement.short_description, '')
        self.assertEqual(movement.description, '')

        movement2 = Movement(
            "toothpicking", timedelta(days=1), "pick your teeth every day!"
        )

        self.assertEqual(movement2.name, "toothpicking")
        self.assertEqual(movement2.interval.days, 1)
        self.assertEqual(movement2.short_description, "pick your teeth every day!")
        self.assertEqual(movement.description, "")

    @patch('gridt.models.update.Update._get_now', return_value=datetime(1996, 3, 15))
    def test_dictify(self, func):
        with self.app_context():
            movement = Movement("flossing", timedelta(days=2), short_description="Hi")
            movement.description = "A long description"
            user1 = User("test1", "test@gmail", "test")
            user2 = User("test2", "test@gmail", "test")
            movement.add_user(user1)
            movement.add_user(user2)
            update = Update(user1, movement)

            user1.save_to_db() # Make sure id == 1
            db.session.add_all([movement, user2, update])
            db.session.commit()

            expected = {
                "name": "flossing",
                "short_description": "Hi",
                "description": "A long description",
                "subscribed": True,
                "interval": {
                    "days": 2,
                    "hours": 0
                },
                "leaders": [
                    {
                        "id": 1,
                        "username": 'test1',
                        "last-update": str(datetime(1996, 3, 15))
                    }
                ]
            }

            self.assertEqual(movement.dictify(user2), expected)

    @patch('gridt.models.update.Update._get_now', return_value=datetime(1996, 3, 15))
    def test_dictify_subscribed(self, func):
        with self.app_context():
            movement = Movement("flossing", timedelta(days=2))
            user1 = User("test1", "test@gmail", "test")
            user2 = User("test2", "test@gmail", "test")
            movement.add_user(user1)
            update = Update(user1, movement)

            user1.save_to_db() # Make sure id == 1
            db.session.add_all([movement, user2, update])
            db.session.commit()

            expected = {
                "name": "flossing",
                "short_description": "",
                "description": "",
                "subscribed": False,
                "interval": {
                    "days": 2,
                    "hours": 0
                },
            }

            self.assertEqual(movement.dictify(user2), expected)

