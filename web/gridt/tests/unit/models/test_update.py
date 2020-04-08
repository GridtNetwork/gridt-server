from gridt.tests.base_test import BaseTest
from gridt.models.signal import Signal
from gridt.models.user import User
from gridt.models.movement import Movement


class SignalTest(BaseTest):
    def test_create(self):
        leader = User("leader", "test@test.com", "password")
        movement = Movement("movement", "daily")
        signal = Signal(leader, movement)

        self.assertEqual(leader, signal.leader)
        self.assertEqual(movement, signal.movement)
