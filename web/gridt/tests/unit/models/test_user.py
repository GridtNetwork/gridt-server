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

    def test_hash(self):
        user = User("username", "test@test.com", "test")
        self.assertTrue(user.verify_password("test"))

    def test_avatar(self):
        user = User("username", "test@test.com", "test")
        self.assertEqual(user.get_email_hash(), "b642b4217b34b1e8d3bd915fc65c4452")
