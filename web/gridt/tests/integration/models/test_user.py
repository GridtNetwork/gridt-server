from gridt.tests.base_test import BaseTest
from gridt.models.user import User


class UserTest(BaseTest):
    def test_find(self):
        with self.app_context():
            self.assertIsNone(User.find_by_name("username"))

            user = User("username", "test@test.com", "password")
            user.save_to_db()

            self.assertEqual(user, User.find_by_name("username"))

    def test_save(self):
        with self.app_context():
            user = User("username", "test@test.com", "password")
            user.save_to_db()

            self.assertIsNotNone(User.query.filter_by(username="username").first())

            user.delete_from_db()

            self.assertIsNone(User.query.filter_by(username="username").first())

    def test_create(self):
        with self.app_context(), nostderr():
            user = User("name", "email", "password", role="role", bio="bio")
            user.save_to_db()

            self.assertIsNotNone(user.id)
            self.assertEqual(user.username, "name")
            self.assertEqual(user.email, "email")
            self.assertEqual(user.role, "role")
            self.assertEqual(user.bio, "bio")

    def test_leaders(self):
        with self.app_context():
            user1 = User("user1", "test1@test.com", "test")
            user2 = User("user2", "test2@test.com", "test")
            user3 = User("user3", "test3@test.com", "test")

            movement = Movement("movement1", "daily")

            assoc1 = MovementUserAssociation(movement, user1, user2)
            assoc2 = MovementUserAssociation(movement, user1, user3)

            db.session.add_all(
                [user1, user2, user3, assoc1, assoc2,]
            )
            db.session.commit()

            self.assertEqual(len(user1.leaders(movement)), 2)
            self.assertIn(user2, user1.leaders(movement))
            self.assertIn(user3, user1.leaders(movement))
    
    def test_leaders_removed(self):
        with self.app_context():
            user1 = User("user1", "test1@test.com", "test")
            user2 = User("user2", "test2@test.com", "test")
            user3 = User("user3", "test3@test.com", "test")
            user4 = User("user4", "test4@test.com", "test")

            movement = Movement("movement1", "daily")

            assoc1 = MovementUserAssociation(movement, user1, user2)
            assoc2 = MovementUserAssociation(movement, user1, user3)
            assoc3 = MovementUserAssociation(movement, user1, user4)
            assoc3.destroy()

            db.session.add_all(
                [user1, user2, user3, user4, assoc1, assoc2, assoc3,]
            )
            db.session.commit()

            self.assertEqual(len(user1.leaders(movement)), 2)
            self.assertIn(user2, user1.leaders(movement))
            self.assertIn(user3, user1.leaders(movement))
