from datetime import timedelta

from gridt.db import db
from gridt.tests.base_test import BaseTest
from gridt.models.movement import Movement
from gridt.models.user import User
from gridt.models.movement_user_association import MovementUserAssociation


class MovementTest(BaseTest):
    def test_crud(self):
        with self.app_context():
            movement = Movement("flossing", timedelta(days=2))

            self.assertIsNone(User.query.filter_by(username="username").first())

            movement.save_to_db()

            self.assertIsNotNone(Movement.query.filter_by(name="flossing").first())

            movement.delete_from_db()

            self.assertIsNone(Movement.query.filter_by(name="flossing").first())

    def test_find_leaders(self):
        with self.app_context():
            user1 = User("user1", "test@test.com", "password")
            user1.save_to_db()
            movement = Movement("movement", timedelta(days=1))
            movement.save_to_db()
            movement.add_user(user1)

            user2 = User("user2", "test@test.com", "password")
            user2.save_to_db()

            self.assertEqual(movement._find_possible_leaders_ids(user1), [])

            user2.movements.append(movement)
            self.assertEqual(movement._find_possible_leaders_ids(user2), [1])
            self.assertEqual(
                movement._find_possible_leaders_ids(user2, exclude=[user1]), []
            )
            self.assertEqual(
                movement._find_possible_leaders_ids(user2, exclude=[1]), []
            )

            movement.add_user(user2)

            user3 = User("user3", "test@test.com", "password")
            user3.save_to_db()
            movement.add_user(user3)

            movement._find_possible_leaders_ids(user2)

            self.assertTrue(user2.id in movement._find_possible_leaders_ids(user1))

    def test_swap_leader(self):
        with self.app_context():
            user1 = User("user1", "test@test.com", "password")
            user2 = User("user2", "test@test.com", "password")
            user3 = User("user3", "test@test.com", "password")
            movement = Movement("movement", timedelta(days=2))
            db.session.add_all([user1, user2, user3, movement])
            db.session.commit()
            movement.add_user(user1)
            movement.add_user(user2)
            movement.add_user(user3)

            self.assertFalse(movement.swap_leader(user1, user2))

            user4 = User("user4", "test@test.com", "password")
            user5 = User("user5", "test@test.com", "password")
            db.session.add_all([user4, user5])
            db.session.commit()

            movement.add_user(user4)
            movement.add_user(user5)

            self.assertTrue(movement.swap_leader(user2, user1))
            self.assertTrue(user1 not in user2.leaders(movement))
            self.assertEqual(len(user2.leaders(movement)), 1)

            self.assertTrue(movement.swap_leader(user1, None))
            self.assertIn(user1.leaders(movement)[0], [user2, user3, user4, user5])
