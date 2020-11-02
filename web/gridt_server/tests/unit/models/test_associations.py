from gridt_server.tests.base_test import BaseTest

from gridt_server.models.movement_user_association import MovementUserAssociation
from gridt_server.models.user import User
from gridt_server.models.movement import Movement

from freezegun import freeze_time
from datetime import datetime


class AssociationTest(BaseTest):
    def test_destroy(self):
        with self.app_context():
            robin = User("robin", "robin@test.com", "password")
            jorn = User("jorn", "jorn@test.com", "password")
            flossing = Movement("flossing", "daily")
            assoc = MovementUserAssociation(flossing, robin, jorn)

            with freeze_time("2020-04-18 22:52:00"):
                assoc.destroy()
            self.assertEqual(
                assoc.destroyed,
                datetime(2020, 4, 18, 22, 52),
                "Mua's 'destroyed' value must be equal to a datetime object.",
            )

    @freeze_time("2020-04-18 21:39:00")
    def test_create(self):
        with self.app_context():
            movement = Movement("flossing", "daily")
            user1 = User("user1", "user1@user.com", "password")
            user2 = User("user2", "user2@user.com", "password")
            mua = MovementUserAssociation(movement, user1, user2)

            self.assertEqual(mua.follower, user1)
            self.assertEqual(mua.leader, user2)
            self.assertEqual(mua.movement, movement)
            self.assertEqual(mua.created, datetime(2020, 4, 18, 21, 39))
            self.assertEqual(mua.destroyed, None)
