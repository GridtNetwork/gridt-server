from datetime import timedelta

from gridt.db import db
from gridt.tests.base_test import BaseTest
from gridt.models.movement import Movement
from gridt.models.user import User
from gridt.models.movement_user_association import MovementUserAssociation


class MovementTest(BaseTest):
    def test_crud(self):
        with self.app_context():
            self.assertIsNone(Movement.query.filter_by(name="flossing").first())

            movement = Movement("flossing", timedelta(days=2))
            movement.save_to_db()

            self.assertIsNotNone(Movement.query.filter_by(name="flossing").first())

            movement.delete_from_db()

            self.assertIsNone(Movement.query.filter_by(name="flossing").first())

    def test_swap_leader(self):
        with self.app_context():
            user1 = User("user1", "test@test.com", "password")
            user2 = User("user2", "test@test.com", "password")
            user3 = User("user3", "test@test.com", "password")
            movement1 = Movement("movement1", timedelta(days=2))

            db.session.add_all([user1, user2, user3, movement1])
            db.session.commit()

            assoc1 = MovementUserAssociation(movement1, user1, user2)
            assoc2 = MovementUserAssociation(movement1, user2, user1)
            assoc3 = MovementUserAssociation(movement1, user1, None)

            self.assertFalse(movement.swap_leader(user1, user2))

            user4 = User("user4", "test@test.com", "password")
            user5 = User("user5", "test@test.com", "password")
            db.session.add_all([user4, user5])
            db.session.commit()

            movement.add_user(user4)
            movement.add_user(user5)

            self.assertTrue(movement.swap_leader(user2, user1))
            self.assertEqual(len(user2.leaders(movement)), 1)

            self.assertTrue(movement.swap_leader(user1, None))
            self.assertIn(user1.leaders(movement)[0], [user2, user3, user4, user5])

    def test_swap_leader(self):
        with self.app_context():
            user1 = User("user1", "test@test.com", "password")
            user2 = User("user2", "test@test.com", "password")
            user3 = User("user3", "test@test.com", "password")
            user4 = User("user4", "test@test.com", "password")
            movement1 = Movement("movement1", timedelta(days=2))
            movement2 = Movement("movement2", timedelta(days=2))

            # Movement 1
            #
            #   3 -> 1 <-> 2
            #        |
            #        v
            #        4
            #
            # ------------------------------------------------------
            # Movement 2
            #
            #   1 <-> 2
            #
            assoc1 = MovementUserAssociation(movement1, user1, user2)
            assoc2 = MovementUserAssociation(movement1, user2, user1)
            assoc3 = MovementUserAssociation(movement1, user3, user1)
            assoc4 = MovementUserAssociation(movement1, user1, user4)
            assoc5 = MovementUserAssociation(movement2, user1, user2)
            assoc6 = MovementUserAssociation(movement2, user2, user1)

            db.session.add_all(
                [
                    user1,
                    user2,
                    user3,
                    user4,
                    movement1,
                    assoc1,
                    assoc2,
                    assoc3,
                    assoc4,
                    assoc5,
                    assoc6,
                ]
            )
            db.session.commit()

            self.assertEqual(movement1.swap_leader(user1, user2), user3)

            with self.assertRaises(ValueError):
                movement1.swap_leader(user1, user2)

            self.assertIsNone(movement2.swap_leader(user1, user2))
