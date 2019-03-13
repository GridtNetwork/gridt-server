import unittest
from datetime import timedelta

from gridt.db import db

from gridt.tests.base_test import BaseTest

from gridt.models.movement_user_association import MovementUserAssociation
from gridt.models.user import User
from gridt.models.movement import Movement


class AssociationTest(BaseTest):
    # @unittest.skip("For speed")
    def test_add_user_to_movement(self):
        with self.app_context():
            robin = User("robin", "test@test.com", "password")
            pieter = User("pieter", "test@test.com", "password")
            jorn = User("jorn", "test@test.com", "password")

            flossing = Movement("flossing", timedelta(days=1))
            running = Movement("running", timedelta(days=1))

            flossing.add_user(robin)
            running.add_user(jorn)

            self.assertTrue(flossing in robin.movements)
            self.assertTrue(robin in flossing.users)
            self.assertTrue(len(flossing.user_associations) == 4)
            self.assertFalse(robin in running.users)
            self.assertFalse(jorn in flossing.users)

            flossing.add_user(pieter)

            pieters_leaders = list(
                map(lambda a: a.leader, pieter.follower_associations)
            )
            self.assertEqual(pieters_leaders, [robin, None, None, None])
            self.assertTrue(robin in pieters_leaders)
            self.assertFalse(jorn in pieters_leaders)

    # @unittest.skip("For speed")
    def test_remove_user_from_movement(self):
        with self.app_context():
            robin = User("robin", "test@test.com", "password")
            pieter = User("pieter", "test@test.com", "password")

            flossing = Movement("flossing", timedelta(days=1))

            flossing.add_user(robin)
            flossing.add_user(pieter)
            flossing.remove_user(robin)

            self.assertFalse(robin in flossing.users)
            self.assertFalse(flossing in robin.movements)
            self.assertTrue(len(robin.follower_associations) == 0)
            self.assertTrue(len(flossing.user_associations) == 4)

            flossing.remove_user(pieter)
            self.assertTrue(len(flossing.user_associations) == 0)

    # @unittest.skip("For speed")
    def test_remove_leader_from_movement(self):
        with self.app_context():
            robin = User("robin", "test@test.com", "password")
            pieter = User("pieter", "test@test.com", "password")

            flossing = Movement("flossing", timedelta(days=1))

            flossing.add_user(robin)
            flossing.add_user(pieter)

            pieters_leaders = list(
                map(lambda a: a.leader, pieter.follower_associations)
            )
            self.assertTrue(robin in pieters_leaders)

            flossing.remove_user(robin)

            pieters_leaders = list(
                map(lambda a: a.leader, pieter.follower_associations)
            )
            self.assertFalse(robin in pieters_leaders)
