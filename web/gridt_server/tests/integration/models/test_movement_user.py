import unittest
from gridt_server.db import db

from gridt_server.tests.base_test import BaseTest

from gridt_server.models.movement_user_association import MovementUserAssociation
from gridt_server.models.user import User
from gridt_server.models.movement import Movement


class AssociationTest(BaseTest):
    def test_association_crud(self):
        with self.app_context():
            self.assertIsNone(MovementUserAssociation.query.get(1))

            assoc = MovementUserAssociation()
            assoc.save_to_db()

            self.assertIsNotNone(MovementUserAssociation.query.get(1))

            assoc.delete_from_db()
            self.assertIsNone(MovementUserAssociation.query.get(1))
