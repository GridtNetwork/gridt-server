from tests.base_test import BaseTest
from models.movement import Movement
from models.user import User

class MovementTest(BaseTest):
    def test_save_to_db(self):
        with self.app_context():
            movement = Movement('flossing')

            self.assertIsNone(User.query.filter_by(username='username').first())

            movement.save_to_db()

            self.assertIsNotNone(Movement.query.filter_by(name='flossing').first())

            movement.delete_from_db()

            self.assertIsNone(Movement.query.filter_by(name='flossing').first())

    def test_movement_user_relations(self):
        with self.app_context():
            user = User('username', 'password')
            user.save_to_db()

            movement = Movement('flossing')
            movement.save_to_db()

            movement.users.append(user)
            self.assertTrue(user in movement.users)
            self.assertTrue(movement in user.movements)

