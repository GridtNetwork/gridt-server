from gridt.tests.base_test import BaseTest
from gridt.models.signal import Signal
from gridt.models.user import User
from gridt.models.movement import Movement


class SignalTest(BaseTest):
    def test_create(self):
        leader = User("leader", "test@test.com", "password")
        movement = Movement("movement", "daily")
        signal1 = Signal(leader, movement)
        signal2 = Signal(leader, movement, "Hello")

        self.assertEqual(leader, signal1.leader)
        self.assertEqual(movement, signal1.movement)
        self.assertEqual(None, signal1.message)

        self.assertEqual("Hello", signal2.message)
