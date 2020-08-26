import lorem
from datetime import datetime

from gridt.db import db

from gridt.models.movement import Movement
from gridt.models.signal import Signal
from gridt.models.user import User

from gridt.tests.base_test import BaseTest


class SwapTest(BaseTest):
    def test_swap_leader(self):
        with self.app_context():
            movement = Movement("Flossing", "daily", "Hi")

            user1 = User("test1", "test1@test.com", "pass")
            user2 = User("test2", "test2@test.com", "pass")
            user3 = User("test3", "test3@test.com", "pass")
            user4 = User("test4", "test4@test.com", "pass")
            user5 = User("test5", "test5@test.com", "pass")

            signal = Signal(user3, movement)
            time_stamp = signal.time_stamp

            db.session.add_all([user1, user2, user2, user2, user2, signal, movement])

            movement.add_user(user1)
            movement.add_user(user2)
            movement.add_user(user3)
            movement.add_user(user4)
            movement.add_user(user5)

            token = self.obtain_token("test1@test.com", "pass")

            resp = self.client.post(
                "/movements/Flossing/leader/5",
                headers={"Authorization": f"JWT {token}"},
            )

    def test_swap_leader_movement_nonexistant(self):
        with self.app_context():
            user1 = User("test", "test1@test.com", "pass")
            user1.save_to_db()

            token = self.obtain_token("test1@test.com", "pass")

            resp = self.client.post(
                "/movements/Flossing/leader/2",
                headers={"Authorization": f"JWT {token}"},
            )

            self.assertEqual(resp.status_code, 404)
            self.assertEqual(
                resp.get_json(), {"message": "This movement does not exist."}
            )

    def test_swap_leader_movement_not_subscribed(self):
        with self.app_context():
            movement = Movement("Flossing", "daily", "Hi")
            movement.save_to_db()
            user1 = User("test1", "test1@test.com", "pass")
            user1.save_to_db()

            token = self.obtain_token("test1@test.com", "pass")

            resp = self.client.post(
                "/movements/Flossing/leader/1",
                headers={"Authorization": f"JWT {token}"},
            )

            self.assertEqual(resp.status_code, 400)
            self.assertEqual(
                resp.get_json(),
                {"message": "User is not subscribed to this movement."},
            )

    def test_swap_leader_not_leader(self):
        with self.app_context():
            movement = Movement("Flossing", "daily", "Hi")
            movement.save_to_db()
            user1 = User("test1", "test1@test.com", "pass")
            user1.save_to_db()
            user2 = User("test2", "test2@test.com", "pass")
            user2.save_to_db()
            movement.add_user(user1)

            token = self.obtain_token("test1@test.com", "pass")

            resp = self.client.post(
                "/movements/Flossing/leader/2",
                headers={"Authorization": f"JWT {token}"},
            )

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
