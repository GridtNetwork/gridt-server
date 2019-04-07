from datetime import timedelta

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

        self.assertEqual(user.verify_password("test"), True)

    def test_leaders(self):
        with self.app_context():
            user1 = User("user1", "test@test.com", "test")
            user2 = User("user2", "test@test.com", "test")
            user3 = User("user3", "test@test.com", "test")
            user4 = User("user4", "test@test.com", "test")

            movement1 = Movement("movement1", timedelta(days=2))
            movement2 = Movement("movement2", timedelta(days=2))

            assoc1 = MovementUserAssociation(movement1, user1, user2)
            assoc2 = MovementUserAssociation(movement1, user1, user3)
            assoc3 = MovementUserAssociation(movement1, user2, user1)
            assoc4 = MovementUserAssociation(movement2, user1, user2)
            assoc5 = MovementUserAssociation(movement2, user2, user1)
            assoc6 = MovementUserAssociation(movement1, user1, None)

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

            self.assertEqual(user1.leaders(movement1), [user2, user3])