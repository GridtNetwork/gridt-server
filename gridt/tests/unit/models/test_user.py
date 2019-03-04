from tests.base_test import BaseTest
from db import db
from models.user import User

class UserTest(BaseTest):
    def test_create(self):
        with self.app_context():
            user1 = User('username', 'password')

            self.assertEqual(user1.username, 'username')
            self.assertEqual(user1.verify_password('password'), True)
            self.assertEqual(user1.role, 'user')

            user2 = User('username2', 'password2', role='administrator')

            self.assertEqual(user2.username, 'username2')
            self.assertEqual(user2.verify_password('password2'), True)
            self.assertEqual(user2.role, 'administrator')

    def test_find(self):
        with self.app_context():
            user1 = User('username', 'password')
            user1.save_to_db()

            self.assertEqual(User.find_by_name('username'), user1)

    def test_hash(self):
        user = User('username', 'password')
        user.hash_password('test')

        self.assertEqual(user.verify_password('test'), True)

