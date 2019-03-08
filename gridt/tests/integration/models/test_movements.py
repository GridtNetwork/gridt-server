from tests.base_test import BaseTest
from models.movement import Movement
from models.user import User


class MovementTest(BaseTest):
    def test_crud(self):
        with self.app_context():
            movement = Movement("flossing")

            self.assertIsNone(User.query.filter_by(username="username").first())

            movement.save_to_db()

            self.assertIsNotNone(Movement.query.filter_by(name="flossing").first())

            movement.delete_from_db()

            self.assertIsNone(Movement.query.filter_by(name="flossing").first())
