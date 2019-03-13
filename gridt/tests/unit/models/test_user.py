from gridt.tests.base_test import BaseTest
from gridt.db import db
from gridt.models.user import User
from gridt.models.movement import Movement
from gridt.models.movement_user_association import MovementUserAssociation


class UserTest(BaseTest):
    def test_create(self):
        with self.app_context():
            user1 = User("username", "password")

            self.assertEqual(user1.username, "username")
            self.assertEqual(user1.verify_password("password"), True)
            self.assertEqual(user1.role, "user")

            user2 = User("username2", "password2", role="administrator")

            self.assertEqual(user2.username, "username2")
            self.assertEqual(user2.verify_password("password2"), True)
            self.assertEqual(user2.role, "administrator")

    def test_find(self):
        with self.app_context():
            user1 = User("username", "password")
            user1.save_to_db()

            self.assertEqual(User.find_by_name("username"), user1)

    def test_hash(self):
        user = User("username", "test")

        self.assertEqual(user.verify_password("test"), True)
