from tests.base_test import BaseTest
from models.user import User

class UserTest(BaseTest):
    def test_hash(self):
        user = User()
        user.hash_password('test')

        self.assertEqual(user.verify_password('test'), True)

