from util.nostderr import nostderr

from gridt.tests.base_test import BaseTest
from gridt.db import db
from gridt.models.user import User
from gridt.models.movement import Movement
from gridt.models.movement_user_association import MovementUserAssociation


class UserTest(BaseTest):
    def test_create(self):
        with self.app_context(), nostderr():
            user1 = User("username", "test@test.com", "password")

            self.assertEqual(user1.username, "username")
            self.assertEqual(user1.verify_password("password"), True)
            self.assertEqual(user1.role, "user")

            user2 = User(
                "username2", "test@test.com", "password2", role="administrator"
            )

            self.assertEqual(user2.username, "username2")
            self.assertEqual(user2.verify_password("password2"), True)
            self.assertEqual(user2.role, "administrator")

            user3 = User("name", "email", "password", role="role", bio="bio")
            user3.save_to_db()

            self.assertIsNotNone(user3.id)
            self.assertEqual(user3.username, "name")
            self.assertEqual(user3.email, "email")
            self.assertEqual(user3.role, "role")
            self.assertEqual(user3.bio, "bio")

    def test_hash(self):
        user = User("username", "test@test.com", "test")
        self.assertTrue(user.verify_password("test"))

    def test_leaders(self):
        with self.app_context():
            user1 = User("user1", "test1@test.com", "test")
            user2 = User("user2", "test2@test.com", "test")
            user3 = User("user3", "test3@test.com", "test")

            movement = Movement("movement1", "daily")

            assoc1 = MovementUserAssociation(movement, user1, user2)
            assoc2 = MovementUserAssociation(movement, user1, user3)

            self.assertEqual(user1.leaders(movement), [user2, user3])
        
    def test_leaders_removed():
        with self.app_context():
            user1 = User("user1", "test1@test.com", "test")
            user2 = User("user2", "test2@test.com", "test")
            user3 = User("user3", "test3@test.com", "test")
            user4 = User("user4", "test4@test.com", "test")

            movement = Movement("movement1", "daily")

            assoc1 = MovementUserAssociation(movement, user1, user2)
            assoc2 = MovementUserAssociation(movement, user1, user3)
            assoc4 = MovementUserAssociation(movement, user1, user4)
            assoc4.destroy()

            self.assertEqual(
                user1.leaders(movement), 
                [user2, user3],
                "Destroyed MUAs must not yield leaders for a user."
            )
