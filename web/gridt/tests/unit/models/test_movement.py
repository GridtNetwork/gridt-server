from datetime import datetime
from unittest.mock import patch

from gridt.tests.base_test import BaseTest
from gridt.db import db
from gridt.models.movement import Movement
from gridt.models.user import User
from gridt.models.update import Update
from gridt.models.movement_user_association import MovementUserAssociation


class MovementTest(BaseTest):
    def test_create(self):
        movement = Movement("movement1", "daily")

        self.assertEqual(movement.name, "movement1")
        self.assertEqual(movement.interval, "daily")
        self.assertEqual(movement.short_description, "")
        self.assertEqual(movement.description, "")

        movement2 = Movement(
            "toothpicking", "twice daily", "pick your teeth every day!"
        )

        self.assertEqual(movement2.name, "toothpicking")
        self.assertEqual(movement2.interval, "twice daily")
        self.assertEqual(movement2.short_description, "pick your teeth every day!")
        self.assertEqual(movement.description, "")

    def test_add_user(self):
        with self.app_context():
            user1 = User("user1", "test1@test.com", "pass")
            user2 = User("user2", "test2@test.com", "pass")
            user3 = User("user3", "test3@test.com", "pass")
            movement1 = Movement("movement1", "daily")
            movement2 = Movement("movement2", "twice daily")

            db.session.add_all([user1, user2, user3, movement1, movement2])
            db.session.commit()

            self.assertEqual(len(user1.follower_associations), 0)
            self.assertEqual(len(user2.follower_associations), 0)
            self.assertEqual(len(movement1.user_associations), 0)
            self.assertEqual(len(movement2.user_associations), 0)

            movement1.add_user(user1)

            self.assertEqual(len(user1.follower_associations), 4)
            self.assertEqual(len(user2.follower_associations), 0)
            self.assertEqual(len(movement1.user_associations), 4)
            self.assertEqual(len(movement2.user_associations), 0)

            movement1.add_user(user2)

            self.assertEqual(len(user1.follower_associations), 4)
            self.assertEqual(len(user2.follower_associations), 4)
            self.assertEqual(len(movement1.user_associations), 8)
            self.assertEqual(len(movement2.user_associations), 0)
            self.assertIn(user1, user2.leaders(movement1))
            self.assertIn(user2, user1.leaders(movement1))

            movement1.add_user(user3)

            self.assertEqual(len(user1.follower_associations), 4)
            self.assertEqual(len(user2.follower_associations), 4)
            self.assertEqual(len(movement1.user_associations), 12)
            self.assertEqual(len(movement2.user_associations), 0)
            self.assertIn(user1, user2.leaders(movement1))
            self.assertIn(user1, user3.leaders(movement1))
            self.assertIn(user2, user1.leaders(movement1))
            self.assertIn(user2, user3.leaders(movement1))
            self.assertIn(user3, user1.leaders(movement1))
            self.assertIn(user3, user2.leaders(movement1))

    def test_find_leaders(self):
        with self.app_context():
            user1 = User("user1", "test1@test", "pass")
            user2 = User("user2", "test2@test", "pass")
            user3 = User("user3", "test3@test", "pass")
            user4 = User("user4", "test4@test", "pass")
            user5 = User("user5", "test5@test", "pass")

            movement1 = Movement("movement1", "twice daily")
            movement2 = Movement("movement2", "daily")

            # Movement 1
            #
            #   1 -> 5   2   4
            #
            # -------------------
            # Movement 2
            #
            #   1 -> 5   3
            #
            assoc1 = MovementUserAssociation(movement1, user1, None)
            assoc2 = MovementUserAssociation(movement1, user2, None)
            assoc3 = MovementUserAssociation(movement1, user1, None)
            assoc4 = MovementUserAssociation(movement1, user4, None)
            assoc5 = MovementUserAssociation(movement1, user5, None)
            assoc6 = MovementUserAssociation(movement1, user1, user5)
            assoc7 = MovementUserAssociation(movement2, user1, user5)
            assoc8 = MovementUserAssociation(movement2, user1, None)
            assoc9 = MovementUserAssociation(movement2, user3, None)

            db.session.add_all(
                [
                    user1,
                    user2,
                    user3,
                    movement1,
                    movement2,
                    assoc1,
                    assoc2,
                    assoc3,
                    assoc4,
                    assoc5,
                    assoc6,
                    assoc7,
                    assoc8,
                    assoc9,
                ]
            )
            db.session.commit()

            self.assertEqual(movement1.find_leaders(user1), [user2, user4])

    def test_remove_user_from_movement(self):
        with self.app_context():
            user1 = User("user1", "test1@test.com", "password")
            user2 = User("user2", "test2@test.com", "password")

            movement1 = Movement("movement1", "daily")

            movement1.add_user(user1)
            movement1.add_user(user2)
            movement1.remove_user(user1)

            self.assertFalse(user1 in movement1.users)
            self.assertFalse(movement1 in user1.movements)
            self.assertTrue(len(user1.follower_associations) == 0)
            self.assertTrue(len(movement1.user_associations) == 4)

            movement1.remove_user(user2)
            self.assertTrue(len(movement1.user_associations) == 0)

    def test_remove_leader_from_movement(self):
        with self.app_context():
            user1 = User("user1", "test1@test.com", "password")
            user2 = User("user2", "test2@test.com", "password")

            movement1 = Movement("movement1", "daily")

            movement1.add_user(user1)
            movement1.add_user(user2)

            user2s_leaders = list(map(lambda a: a.leader, user2.follower_associations))
            self.assertTrue(user1 in user2s_leaders)

            movement1.remove_user(user1)

            user2s_leaders = list(map(lambda a: a.leader, user2.follower_associations))
            self.assertFalse(user1 in user2s_leaders)

    @patch("gridt.models.update.Update._get_now", return_value=datetime(1996, 3, 15))
    def test_dictify(self, func):
        with self.app_context():
            movement = Movement("movement1", "daily", short_description="Hi")
            movement.description = "A long description"
            user1 = User("test1", "test1@test.com", "test")
            user2 = User("test2", "test2@test.com", "test")
            movement.add_user(user1)
            movement.add_user(user2)
            update = Update(user1, movement)

            user1.save_to_db()  # Make sure id == 1
            db.session.add_all([movement, user2, update])
            db.session.commit()

            expected = {
                "id": 1,
                "name": "movement1",
                "short_description": "Hi",
                "description": "A long description",
                "subscribed": True,
                "interval": "daily",
                "leaders": [
                    {
                        "id": 1,
                        "username": "test1",
                        "last_update": str(datetime(1996, 3, 15).astimezone()),
                    }
                ],
            }

            self.assertEqual(movement.dictify(user2), expected)

    @patch("gridt.models.update.Update._get_now", return_value=datetime(1996, 3, 15))
    def test_dictify_subscribed(self, func):
        with self.app_context():
            movement = Movement("movement1", "twice daily")
            user1 = User("test1", "test1@gmail", "test")
            user2 = User("test2", "test2@gmail", "test")
            movement.add_user(user1)
            update = Update(user1, movement)

            user1.save_to_db()  # Make sure id == 1
            db.session.add_all([movement, user2, update])
            db.session.commit()

            expected = {
                "name": "movement1",
                "id": 1,
                "short_description": "",
                "description": "",
                "subscribed": False,
                "interval": "twice daily",
            }
            self.assertEqual(movement.dictify(user2), expected)
