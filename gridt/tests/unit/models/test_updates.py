from datetime import timedelta

from gridt.tests.base_test import BaseTest
from gridt.models.updates import Update
from gridt.models.user import User
from gridt.models.movement import Movement


class UpdateTest(BaseTest):
    def test_create(self):
        leader = User("leader", "test@test.com", "password")
        movement = Movement("movement", timedelta(days=1))
        update = Update(leader, movement)

        self.assertEqual(leader, update.leader)
        self.assertEqual(movement, update.movement)

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()
