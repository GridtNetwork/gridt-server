import unittest
from gridt.db import db

from gridt.tests.base_test import BaseTest

from gridt.models.movement_user_association import MovementUserAssociation
from gridt.models.user import User
from gridt.models.movement import Movement


class AssociationTest(BaseTest):
    def test_association_crud(self):
        with self.app_context():
            self.assertIsNone(MovementUserAssociation.find_by_id(1))

            assoc = MovementUserAssociation()
            assoc.save_to_db()

            self.assertIsNotNone(MovementUserAssociation.find_by_id(1))

            assoc.delete_from_db()
            self.assertIsNone(MovementUserAssociation.find_by_id(1))

    def test_find_by(self):
        with self.app_context():
            user = User("user", "password")
            user.save_to_db()
            movement = Movement("movement_name")
            movement.save_to_db()

            self.assertIsNone(MovementUserAssociation.find_by_id(1))
            self.assertIsNone(MovementUserAssociation.find_by_follower(user))
            self.assertIsNone(MovementUserAssociation.find_by_movement(movement))

            asso = MovementUserAssociation(follower=user, movement=movement)

            self.assertIsNotNone(MovementUserAssociation.find_by_id(1))
            self.assertIsNotNone(MovementUserAssociation.find_by_follower(user))
            self.assertIsNotNone(MovementUserAssociation.find_by_movement(movement))
