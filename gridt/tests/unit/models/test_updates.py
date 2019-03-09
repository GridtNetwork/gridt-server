from tests.base_test import BaseTest
from models.updates import Update
from models.user import User
from models.movement import Movement

class UpdateTest(BaseTest):
    def test_create(self):
        leader = User('leader', 'password')
        movement = Movement('movement')
        update = Update(leader, movement)

        self.assertEqual(leader, update.leader)
        self.assertEqual(movement, update.movement)

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()
