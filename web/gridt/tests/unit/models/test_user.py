from util.nostderr import nostderr

from flask import current_app
from freezegun import freeze_time
import jwt

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

    def test_get_password_reset_token(self):
        with self.app_context():
            user = User("username", "test@test.com", "password")
            with freeze_time("2020-04-18 22:10:00"):
                self.assertEqual(
                    jwt.decode(
                        user.get_password_reset_token(),
                        current_app.config["SECRET_KEY"],
                        algorithms=["HS256"],
                    ),
                    {"user_id": user.id, "exp": 1587255000.0},
                )

    def test_get_email_reset_token(self):
        with self.app_context():
            user = self.create_user()
            new_email = "new@email.com"
            with freeze_time("2020-04-18 22:10:00"):
                self.assertEqual(
                    jwt.decode(
                        user.get_email_change_token(new_email),
                        current_app.config["SECRET_KEY"],
                        algorithms=["HS256"],
                    ),
                    {"user_id": user.id, "new_email": new_email, "exp": 1587255000.0}
                )
