import json
import lorem
from unittest.mock import patch
from datetime import datetime
from freezegun import freeze_time

from gridt.tests.base_test import BaseTest
from gridt.db import db
from gridt.models import User, Movement, Signal, MovementUserAssociation


class MovementTest(BaseTest):
    def test_crud(self):
        with self.app_context():
            self.assertIsNone(Movement.query.filter_by(name="flossing").first())

            movement = Movement("flossing", "daily")
            movement.save_to_db()

            self.assertIsNotNone(Movement.query.filter_by(name="flossing").first())

            movement.delete_from_db()

            self.assertIsNone(Movement.query.filter_by(name="flossing").first())

    def test_swap_leader(self):
        """
        1 <-> 2
        4 5
        """
        with self.app_context():
            user1 = User("user1", "test1@test.com", "password")
            user2 = User("user2", "test2@test.com", "password")
            user3 = User("user3", "test3@test.com", "password")
            movement = Movement("movement1", "daily")

            db.session.add_all([user1, user2, user3, movement])
            db.session.commit()

            assoc1 = MovementUserAssociation(movement, user1, user2)
            assoc2 = MovementUserAssociation(movement, user2, user1)

            self.assertFalse(movement.swap_leader(user1, user2))

            user4 = User("user4", "test4@test.com", "password")
            user5 = User("user5", "test5@test.com", "password")
            assoc3 = MovementUserAssociation(movement, user4, None)
            assoc4 = MovementUserAssociation(movement, user5, None)
            db.session.add_all([user4, user5, assoc1, assoc2, assoc3, assoc4])
            db.session.commit()

            # Will not catch possible mistake (movement.swap_leader(..., ...) == user3)
            # 2/3 of the time
            self.assertIn(movement.swap_leader(user2, user1), [user4, user5])
            self.assertEqual(len(user2.leaders(movement)), 1)

    def test_swap_leader_complicated(self):
        """
        Movement 1

              3 -> 1 <-> 2
                   |
                   v
                   4

        ------------------------------------------------------
        Movement 2

            1 <-> 5

        """
        with self.app_context():
            user1 = User("user1", "test1@test.com", "password")
            user2 = User("user2", "test2@test.com", "password")
            user3 = User("user3", "test3@test.com", "password")
            user4 = User("user4", "test4@test.com", "password")
            user5 = User("user5", "test5@test.com", "password")
            movement1 = Movement("movement1", "daily")
            movement2 = Movement("movement2", "daily")

            assoc1 = MovementUserAssociation(movement1, user1, user2)
            assoc2 = MovementUserAssociation(movement1, user2, user1)
            assoc3 = MovementUserAssociation(movement1, user3, user1)
            assoc4 = MovementUserAssociation(movement1, user1, user4)
            assoc5 = MovementUserAssociation(movement2, user1, user5)
            assoc6 = MovementUserAssociation(movement2, user5, user1)

            db.session.add_all(
                [
                    user1,
                    user2,
                    user3,
                    user4,
                    movement1,
                    movement2,
                    assoc1,
                    assoc2,
                    assoc3,
                    assoc4,
                    assoc5,
                    assoc6,
                ]
            )
            db.session.commit()

            new_leader = movement1.swap_leader(user1, user2)
            # Make sure that it is actually saved in the database!
            db.session.rollback()
            self.assertEqual(new_leader, user3)

            with self.assertRaises(ValueError):
                movement1.swap_leader(user1, user2)

            self.assertIsNone(movement2.swap_leader(user1, user5))

    def test_add_user(self):
        with self.app_context():
            user1 = User("user1", "test1@test.com", "pass")
            user2 = User("user2", "test2@test.com", "pass")
            user3 = User("user3", "test3@test.com", "pass")
            movement1 = Movement("movement1", "daily")
            movement2 = Movement("movement2", "twice daily")

            db.session.add_all(
                [user1, user2, user3, movement1, movement2,]
            )
            db.session.commit()

            self.assertEqual(user1.follower_associations, [])
            self.assertEqual(user1.leaders(movement1), [])
            self.assertEqual(user2.follower_associations, [])
            self.assertEqual(user2.leaders(movement1), [])
            self.assertEqual(movement1.user_associations, [])
            self.assertEqual(movement2.user_associations, [])

            movement1.add_user(user1)

            self.assertEqual(len(user1.follower_associations), 1)
            self.assertEqual(len(user2.follower_associations), 0)
            self.assertEqual(len(movement1.user_associations), 1)
            self.assertEqual(len(movement2.user_associations), 0)
            self.assertEqual(user1.leaders(movement1), [])

            movement1.add_user(user2)

            self.assertEqual(len(user1.follower_associations), 2)
            self.assertEqual(len(user2.follower_associations), 1)
            self.assertEqual(len(movement1.user_associations), 3)
            self.assertEqual(len(movement2.user_associations), 0)
            self.assertEqual(user1.leaders(movement1), [user2])
            self.assertEqual(user2.leaders(movement1), [user1])

            movement1.add_user(user3)

            self.assertEqual(len(user1.follower_associations), 3)
            self.assertEqual(len(user2.follower_associations), 2)
            self.assertEqual(len(user3.follower_associations), 2)
            self.assertEqual(len(movement1.user_associations), 7)
            self.assertEqual(len(movement2.user_associations), 0)
            self.assertEqual(set(user1.leaders(movement1)), set([user2, user3]))
            self.assertEqual(set(user2.leaders(movement1)), set([user1, user3]))
            self.assertEqual(set(user3.leaders(movement1)), set([user1, user2]))

    def test_find_leaders(self):
        """
        Movement 1

          1 -> 5   2   4

        -------------------
        Movement 2

          1 -> 5   3
        """
        with self.app_context():
            user1 = User("user1", "test1@test", "pass")
            user2 = User("user2", "test2@test", "pass")
            user3 = User("user3", "test3@test", "pass")
            user4 = User("user4", "test4@test", "pass")
            user5 = User("user5", "test5@test", "pass")

            movement1 = Movement("movement1", "twice daily")
            movement2 = Movement("movement2", "daily")

            assoc1 = MovementUserAssociation(movement1, user1, user2)
            assoc2 = MovementUserAssociation(movement1, user1, user4)
            assoc3 = MovementUserAssociation(movement1, user1, user5)
            assoc4 = MovementUserAssociation(movement1, user2, None)
            assoc5 = MovementUserAssociation(movement1, user3, None)
            assoc6 = MovementUserAssociation(movement1, user4, None)
            assoc7 = MovementUserAssociation(movement1, user5, None)
            assoc8 = MovementUserAssociation(movement2, user1, user3)
            assoc9 = MovementUserAssociation(movement2, user1, user5)
            assoc10 = MovementUserAssociation(movement2, user2, None)
            assoc11 = MovementUserAssociation(movement2, user3, None)
            assoc12 = MovementUserAssociation(movement2, user4, None)
            assoc13 = MovementUserAssociation(movement2, user5, None)

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
                    assoc10,
                    assoc11,
                    assoc12,
                    assoc13,
                ]
            )
            db.session.commit()

            # Set because order does not matter
            self.assertEqual(set(movement1.find_leaders(user1)), {user3})
            self.assertEqual(set(movement2.find_leaders(user1)), {user2, user4})

            assoc1.destroy()

            self.assertEqual(set(movement1.find_leaders(user1)), {user2, user3})
            self.assertEqual(set(movement2.find_leaders(user1)), {user2, user4})

    def test_remove_user_from_movement(self):
        with self.app_context():
            user1 = User("user1", "test1@test.com", "password")

            movement1 = Movement("movement1", "daily")

            mua1 = MovementUserAssociation(movement1, user1, None)
            mua1.save_to_db()

            with freeze_time("2020-04-18 22:10:00"):
                movement1.remove_user(user1)

            self.assertFalse(user1 in movement1.current_users)
            self.assertFalse(movement1 in user1.current_movements)

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

    def test_one_leader_removed(self):
        with self.app_context():
            user1 = User("user1", "test1@test.com", "pass")
            user2 = User("user2", "test2@test.com", "pass")
            user3 = User("user3", "test3@test.com", "pass")
            user4 = User("user4", "test4@test.com", "pass")
            user5 = User("user5", "test5@test.com", "pass")
            user6 = User("user6", "test6@test.com", "pass")

            movement = Movement("movement1", "daily")

            db.session.add_all(
                [user1, user2, user3, user4, user5, user6, movement,]
            )

            movement.add_user(user1)
            movement.add_user(user2)
            movement.add_user(user3)
            movement.add_user(user4)
            movement.add_user(user5)
            movement.add_user(user6)

            self.assertEqual(set(user1.leaders(movement)), {user2, user3, user4, user5})
            self.assertEqual(len(user1.follower_associations), 5)

            movement.remove_user(user5)

            self.assertEqual(set(user1.leaders(movement)), {user2, user3, user4, user6})
            self.assertEqual(len(user1.follower_associations), 6)

    def test_last_leader_removed(self):
        with self.app_context():
            user1 = User("user1", "test1@test.com", "password")
            user2 = User("user2", "test2@test.com", "password")

            movement = Movement("movement", "daily")

            db.session.add_all(
                [user1, user2, movement,]
            )
            db.session.commit()

            movement.add_user(user1)
            movement.add_user(user2)

            user2_all_leaders = list(
                map(lambda a: a.leader, user2.follower_associations)
            )
            self.assertEqual(user2_all_leaders, [user1])
            self.assertEqual(user2.leaders(movement), [user1])

            movement.remove_user(user1)

            user2_all_leaders = list(
                map(lambda a: a.leader, user2.follower_associations)
            )
            self.assertEqual(set(user2_all_leaders), set([None, user1]))
            self.assertEqual(user2.leaders(movement), [])

    def test_swap_leader(self):
        with self.app_context():
            user1 = User("user1", "test1@test.com", "password")
            user2 = User("user2", "test2@test.com", "password")
            user3 = User("user3", "test3@test.com", "password")

            movement = Movement("movement", "daily")

            mua1 = MovementUserAssociation(movement, user1, user2)
            mua2 = MovementUserAssociation(movement, user3, None)

            db.session.add_all(
                [user1, user2, user3, movement, mua1, mua2,]
            )
            db.session.commit()

            self.assertEqual(set(user1.leaders(movement)), {user2})

            movement.swap_leader(user1, user2)

            user1_all_leaders = list(
                map(lambda a: a.leader, user1.follower_associations)
            )

            self.assertEqual(set(user1_all_leaders), {user2, user3})
            self.assertEqual(set(user1.leaders(movement)), {user3})

    def test_leaderless(self):
        with self.app_context():
            movement1 = Movement("test1", "daily")
            movement2 = Movement("test2", "daily")

            for i in range(6):
                user = User(f"user{i}", f"user{i}@email.com", "pass")
                user.save_to_db()
            users = User.query.all()

            MUA = MovementUserAssociation
            muas = [
                MUA(movement1, users[0], users[1]),
                MUA(movement1, users[0], users[2]),
                MUA(movement1, users[0], users[3]),
                MUA(movement1, users[1], users[0]),
                MUA(movement1, users[1], users[2]),
                MUA(movement1, users[1], users[3]),
                MUA(movement1, users[2], users[1]),
                MUA(movement1, users[2], users[5]),
                MUA(movement1, users[2], users[3]),
                MUA(movement1, users[2], users[4]),
                MUA(movement1, users[3], None),
                MUA(movement1, users[4], None),
                MUA(movement1, users[5], None),
                MUA(movement2, users[0], users[1]),
                MUA(movement2, users[0], users[2]),
                MUA(movement2, users[0], users[3]),
                MUA(movement2, users[1], None),
                MUA(movement2, users[2], None),
                MUA(movement2, users[3], None),
            ]
            db.session.add_all(muas)
            db.session.commit()

            self.assertEqual(
                set(movement1.find_leaderless(users[0])), set(users[3:]),
            )
            self.assertEqual(set(movement2.find_leaderless(users[0])), set(users[1:4]))

            mua1 = MUA.query.filter(MUA.id == 1).one()
            mua1.destroy()
            mua1.save_to_db()

            self.assertEqual(
                set(movement1.find_leaderless(users[0])), set(users[3:]),
            )
            self.assertEqual(set(movement2.find_leaderless(users[0])), set(users[1:4]))

            mua2 = MUA.query.filter(
                MUA.follower_id == users[1].id,
                MUA.leader_id == users[2].id,
                MUA.movement_id == movement1.id,
            ).one()
            mua2.destroy()
            mua2.save_to_db()

            self.assertEqual(
                set(movement1.find_leaderless(users[0])),
                set([users[3], users[4], users[5]]),
            )
            self.assertEqual(set(movement2.find_leaderless(users[0])), set(users[1:4]))

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
