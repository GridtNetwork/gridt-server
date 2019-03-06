from db import db

from tests.base_test import BaseTest

from models.user import User
from models.movement import Movement


class AssociationTest(BaseTest):
    def test_add_user_to_movement(self):
        with self.app_context():
            robin = User('robin', 'password')
            pieter = User('pieter', 'password')

            flossing = Movement('flossing')
            running = Movement('running')

            db.session.add_all([robin, pieter, flossing, running])
            db.session.commit()

            flossing.add_user(robin)

            self.assertTrue(flossing in robin.movements)
            self.assertTrue(robin in flossing.users)
            self.assertTrue(len(flossing.user_associations) == 4)

            flossing.add_user(pieter)

            pieters_flossing_leaders = list(
                map(lambda a: a.leader, pieter.follower_associations)
            )
            self.assertTrue(robin in pieters_flossing_leaders)

