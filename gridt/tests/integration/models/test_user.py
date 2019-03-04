from tests.base_test import BaseTest
from models.user import User

class UserTest(BaseTest):
    def test_find(self):
        with self.app_context():
            self.assertIsNone(User.find_by_name('username'))

            user = User('username', 'password')

            user.save_to_db()

            self.assertEqual(user, User.find_by_name('username'))


    def test_save(self):
        with self.app_context():
            user = User('username', 'password')
            user.save_to_db()

            self.assertIsNotNone(User.query.filter_by(username='username').first())

            user.delete_from_db()

            self.assertIsNone(User.query.filter_by(username='username').first())
