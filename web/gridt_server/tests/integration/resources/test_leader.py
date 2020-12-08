from freezegun import freeze_time

from gridt_server.tests.base_test import BaseTest


class SwapTest(BaseTest):
    def test_swap_leader(self):
        # check post request to leader resource calls swap_leader
        pass


class LeaderProfileTest(BaseTest):
    def test_get_leader_profile(self):
        # check get request to leader resource calls get_leader
        pass
