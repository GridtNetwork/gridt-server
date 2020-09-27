import lorem
from datetime import datetime

from gridt.db import db

from gridt.models.movement import Movement
from gridt.models.signal import Signal
from gridt.models.user import User

from gridt.tests.base_test import BaseTest


class SwapTest(BaseTest):
    def test_swap_leader_correctly(self):
        with self.app_context():
            movement = self.create_movement()
            # Create six users, the first five of which
            # all follow each other. The sixth has no followers.
            for user in range(5):
                self.create_user_in_movement(movement)
            user6 = self.create_user_in_movement(movement)

            signal = self.signal_as_user(self.users[0], self.movements[0])

            expected = user6.dictify()
            expected["last_signal"] = None

            # Test that the fifth user can be replaced
            # with the sixth user.
            resp = self.request_as_user(
                self.users[0], "POST", f"/movements/{movement.id}/leader/5", json={}
            )

            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.get_json(), expected)

    def test_swap_leader_no_available_leader(self):
        with self.app_context():
            movement = self.create_movement()
            user1 = self.create_user_in_movement(movement)
            self.create_user_in_movement(movement)

            signal = self.signal_as_user(self.users[0], self.movements[0])
            time_stamp = signal.time_stamp

            resp = self.request_as_user(
                self.users[0], "POST", f"/movements/{movement.id}/leader/2", json={}
            )

            self.assertEqual(resp.status_code, 400)
            self.assertEqual(
                resp.get_json(),
                {"message": "Could not find leader to replace the current one."},
            )

    def test_swap_leader_movement_nonexistant(self):
        with self.app_context():
            user = self.create_user()

            resp = self.request_as_user(self.users[0], "POST", "/movements/1/leader/2")

            self.assertEqual(resp.status_code, 404)
            self.assertEqual(
                resp.get_json(), {"message": "This movement does not exist."}
            )

    def test_swap_leader_movement_not_subscribed(self):
        with self.app_context():
            movement = self.create_movement()
            user = self.create_user()

            resp = self.request_as_user(self.users[0], "POST", "/movements/1/leader/2")

            self.assertEqual(resp.status_code, 400)
            self.assertEqual(
                resp.get_json(),
                {"message": "User is not subscribed to this movement."},
            )

    def test_swap_leader_not_leader(self):
        with self.app_context():
            movement = self.create_movement()
            user1 = self.create_user_in_movement(movement)
            user2 = self.create_user()

            resp = self.request_as_user(self.users[0], "POST", "/movements/1/leader/2")

            self.assertEqual(resp.status_code, 400)
            self.assertEqual(
                resp.get_json(), {"message": "User is not following this leader."}
            )


class LeaderProfileTest(BaseTest):
    def test_get_leader_profile(self):
        with self.app_context():
            self.maxDiff = None
            movement = self.create_movement()
            follower = self.create_user_in_movement(movement, generate_bio=True)
            self.create_user_in_movement(movement, generate_bio=True)
            self.create_user_in_movement(movement, generate_bio=True)
            self.create_user_in_movement(movement, generate_bio=True)

            follower_dict = self.users[0]
            leader = follower.leaders(movement)[0]
            leader_dict = self.users[1]

            dates = [
                datetime(2019, 7, 14, 12),
                datetime(2018, 10, 27, 16),
                datetime(1996, 3, 15, 0),
                datetime(1995, 1, 15, 12),
            ]

            signals = [
                self.signal_as_user(
                    leader_dict, movement, message=str(i), moment=date
                ).dictify()
                for i, date in enumerate(dates)
            ]
            signals = signals[:3]

            resp = self.request_as_user(
                follower_dict, "GET", f"/movements/{movement.id}/leader/{leader.id}"
            )
            expected = leader_dict.copy()
            del expected["password"]
            del expected["email"]
            expected["message_history"] = signals

            self.assertEqual(len(resp.get_json()["message_history"]), 3)
            self.assertEqual(resp.get_json(), expected)
