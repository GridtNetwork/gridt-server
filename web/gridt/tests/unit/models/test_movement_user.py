from gridt.tests.base_test import BaseTest

from gridt.models.movement_user_association import MovementUserAssociation
from gridt.models.user import User
from gridt.models.movement import Movement


class AssociationTest(BaseTest):
    def test_crud(self):
        with self.app_context():
            robin = User("robin", "robin@test.com", "password")
            robin.save_to_db()
            jorn = User("jorn", "jorn@test.com", "password")
            jorn.save_to_db()
            flossing = Movement("flossing", "daily")
            flossing.save_to_db()

            self.assertIsNone(MovementUserAssociation.query.get(1))

            assoc = MovementUserAssociation(flossing, robin, jorn)
            assoc.save_to_db()

            self.assertIsNotNone(MovementUserAssociation.query.get(1))

            assoc.delete_from_db()

            self.assertIsNone(MovementUserAssociation.query.get(1))
