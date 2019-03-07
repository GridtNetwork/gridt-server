from db import db

from tests.base_test import BaseTest

from models.user import User
from models.movement import Movement


class AssociationTest(BaseTest):
    def test_add_user_to_movement(self):
        with self.app_context():
            robin = User("robin", "password")
            pieter = User("pieter", "password")
            jorn = User("jorn", "password")

            flossing = Movement("flossing")
            running = Movement("running")

            db.session.add_all([robin, pieter, jorn, flossing, running])
            db.session.commit()

            flossing.add_user(robin)
            running.add_user(jorn)

            self.assertTrue(flossing in robin.movements)
            self.assertTrue(robin in flossing.users)
            self.assertTrue(len(flossing.user_associations) == 4)
            self.assertFalse(robin in running.users)
            self.assertFalse(jorn in flossing.users)

            flossing.add_user(pieter)

            pieters_flossing_leaders = list(
                map(lambda a: a.leader, pieter.follower_associations)
            )
            self.assertTrue(robin in pieters_flossing_leaders)
            self.assertFalse(jorn in pieters_flossing_leaders)
