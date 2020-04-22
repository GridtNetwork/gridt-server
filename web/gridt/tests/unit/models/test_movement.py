from datetime import datetime
from unittest.mock import patch
from freezegun import freeze_time

from gridt.tests.base_test import BaseTest
from gridt.db import db
from gridt.models.movement import Movement
from gridt.models.user import User
from gridt.models.signal import Signal
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
            
            # To make sure the following is true, look at
            # Movement.add_user()
            self.assertEqual(len(user1.follower_associations), 0)
            self.assertEqual(len(user2.follower_associations), 0)
            self.assertEqual(len(movement1.user_associations), 0)
            self.assertEqual(len(movement2.user_associations), 0)

            movement1.add_user(user1)
            self.assertEqual(len(user1.follower_associations), 1)
            self.assertEqual(len(user2.follower_associations), 0)
            self.assertEqual(len(movement1.user_associations), 1)
            self.assertEqual(len(movement2.user_associations), 0)

            movement1.add_user(user2)
            self.assertEqual(len(user1.follower_associations), 1)
            self.assertEqual(len(user2.follower_associations), 1)
            self.assertEqual(len(movement1.user_associations), 2)
            self.assertEqual(len(movement2.user_associations), 0)
            self.assertIn(user1, user2.leaders(movement1))
            self.assertIn(user2, user1.leaders(movement1))

            movement1.add_user(user3)
            self.assertEqual(len(user1.follower_associations), 2)
            self.assertEqual(len(user2.follower_associations), 2)
            self.assertEqual(len(movement1.user_associations), 6)
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
            assoc10 = MovementUserAssociation(movement2, user4, None)
            assoc10.destroy()

            db.session.add_all(
                [
                    user1,
                    user2,
                    user3,
                    user4,
                    user5,
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
            self.assertEqual(movement2.find_leaders(user3), [user1, user4])

    def test_remove_user_from_movement(self):
        with self.app_context():
            user1 = User("user1", "test1@test.com", "password")

            movement1 = Movement("movement1", "daily")

            mua1 = MovementUserAssociation(movement1, user1, None)
            
            with freeze_time("2020-04-18 22:10:00"):
                movement1.remove_user(user1)

            self.assertFalse(user1 in movement1.users)
            self.assertFalse(movement1 in user1.movements)
            self.assertEqual(
                len(user1.follower_associations), 
                1,
                "Mua must still be present after destruction.",
            )
            self.assertEqual(
                user1.follower_associations[0].destroyed,
                datetime(2020, 4, 18, 22, 10),
                "Mua must be destroyed when user is removed from movement.",
            )
            self.assertTrue(len(movement1.user_associations) == 0)

    def test_remove_leader_from_movement(self):
        with self.app_context():
            user1 = User("user1", "test1@test.com", "password")
            user2 = User("user2", "test2@test.com", "password")

            movement = Movement("movement", "daily")

            movement.add_user(user1)
            movement.add_user(user2)

            user2s_leader_assoc = list(map(lambda a: a.leader, user2.follower_associations))
            self.assertTrue(user1 in user2s_leader_assoc)
            self.assertEqual(user2.leaders(movement), [user1])

            movement.remove_user(user1)

            user2_all_leaders = list(map(lambda a: a.leader, user2.follower_associations))
            self.assertTrue(user1 in user2_all_leaders)
            self.assertEqual(user2.leaders(movement), [])

            # To test whether leaders are not empty after removing a leader. (separate test)


    def test_swap_leader(self):
        with self.app_context():
            user1 = User("user1", "test1@test.com", "password")
            user2 = User("user2", "test2@test.com", "password")
            user3 = User("user3", "test3@test.com", "password")
            user4 = User("user4", "test4@test.com", "password")

            movement = Movement("movement", "daily")

            mua1 = MovementUserAssociation(movement, user1, user2)
            mua2 = MovementUserAssociation(moveemnt, user1, user3)
            self.assertEqual(user1.leaders(movement), user2)

            movement.swap_leader(user1, user2)

            user1_all_leaders = list(map(lambda a: a.leader, user1,follower_relations))
            self.assertEqual(user1_all_leaders, [user2, user3, user4])
            self.assertEqual(user1.leaders(movement), [user3, user4])

    @patch("gridt.models.signal.Signal._get_now", return_value=datetime(1996, 3, 15))
    def test_dictify(self, func):
        with self.app_context():
            movement = Movement("movement1", "daily", short_description="Hi")
            movement.description = "A long description"
            movement.save_to_db()
            self.movements.append(movement)

            self.create_user_in_movement(movement)
            self.create_user_in_movement(movement, generate_bio=True)

            now = datetime(1995, 1, 15, 12)
            later = datetime(1996, 3, 15, 8)

            message = "This is a message"

            self.signal_as_user(self.users[0], movement, moment=now)
            self.signal_as_user(self.users[1], movement, message=message, moment=later)

            user_dict = self.users[0]
            del user_dict["password"]
            del user_dict["email"]
            user_dict["last_signal"] = {"time_stamp": str(now.astimezone())}

            expected = {
                "id": 1,
                "name": "movement1",
                "short_description": "Hi",
                "description": "A long description",
                "subscribed": True,
                "interval": "daily",
                "last_signal_sent": {"time_stamp": str(later.astimezone())},
                "leaders": [user_dict],
            }
            user = User.find_by_id(self.users[1]["id"])
            self.assertEqual(movement.dictify(user), expected)

    @patch("gridt.models.signal.Signal._get_now", return_value=datetime(1996, 3, 15))
    def test_dictify_subscribed(self, func):
        with self.app_context():
            movement = Movement("movement1", "twice daily")
            user1 = User("test1", "test1@gmail", "test")
            user2 = User("test2", "test2@gmail", "test")
            movement.add_user(user1)
            signal = Signal(user1, movement)

            user1.save_to_db()  # Make sure id == 1
            db.session.add_all([movement, user2, signal])
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
