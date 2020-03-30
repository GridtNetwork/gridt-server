import unittest
from gridt.db import db

from gridt.tests.base_test import BaseTest

from gridt.models.movement_user_association import MovementUserAssociation
from gridt.models.user import User
from gridt.models.movement import Movement


class AssociationTest(BaseTest):
    def test_association_crud(self):
        with self.app_context():
            self.assertIsNone(MovementUserAssociation.query.get(1))

            assoc = MovementUserAssociation()
            assoc.save_to_db()

            self.assertIsNotNone(MovementUserAssociation.query.get(1))

            assoc.delete_from_db()
            self.assertIsNone(MovementUserAssociation.query.get(1))
