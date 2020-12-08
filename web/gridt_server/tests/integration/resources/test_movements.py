import json
from freezegun import freeze_time
from unittest.mock import patch
from datetime import datetime

from gridt_server.tests.base_test import BaseTest


class MovementsTest(BaseTest):

    # patch mock jwt_required
    # (Look at #89 for a solution)
    def test_get_movements(self):
        with self.app_context():
            resp = self.client.get(
                "/movements", headers={"Authorization": f"JWT {token}"}
            )
            # Check that we get 200

    # patch mock jwt_required
    def test_post_successful(self):
        with self.app_context():
            movement_dict = {
                "name": "movement",
                "short_description": "Hi, hello this is a test",
                "interval": "daily",
            }

            resp = self.request_as_user(
                self.users[0], "POST", "/movements", json=movement_dict,
            )  # change this to self.client.post()

            self.assertEqual(
                json.loads(resp.data), {"message": "Successfully created movement."},
            )
            self.assertEqual(resp.status_code, 201)
            # Check that new_movement is called

    # patch mock jwt_required
    def test_single_movement_by_name(self):  # rename to by_id
        with self.app_context():
            resp1 = self.client.get(
                "/movements/1", headers={"Authorization": f"JWT {token}"},
            )
            self.assertEqual(resp1.status_code, 200)
            # Check that get_movement is called


class SubscribeTest(BaseTest):

    # patch mock jwt_required
    def test_subscribe(self):
        with self.app_context():
            resp = self.client.put(
                "/movements/1/subscriber", headers={"Authorization": f"JWT {token}"},
            )
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(
                json.loads(resp.data),
                {"message": "Successfully subscribed to this movement."},
            )
            # Check that subscribe is called
            
    # patch mock jwt_required
    def test_unsubscribe(self):
        with self.app_context():
            # define an id to replace movement.id

            resp = self.request_as_user(
                self.users[0], "DELETE", f"/movements/{movement.id}/subscriber",
            )  # should be changed to self.client.delete

            self.assertEqual(resp.status_code, 200)
            self.assertEqual(
                json.loads(resp.data),
                {"message": "Successfully unsubscribed from this movement."},
            )
            # Check that remove_user_from_movement is called


class NewSignalTest(BaseTest):

    # patch mock jwt_required
    def test_create_new_signal(self):
        with self.app_context(), freeze_time("1996-03-15"):
            resp = self.client.post(
                "/movements/1/signal", headers={"Authorization": f"JWT {token}"},
            )

            self.assertEqual(
                json.loads(resp.data), {"message": "Successfully created signal."},
            )
            self.assertEqual(resp.status_code, 201)
            # Check that send_signal is called


class SubscriptionsResourceTest(BaseTest):

    # patch mock jwt_required
    def test_get_subscriptions(self):
        with self.app_context():
            resp = self.request_as_user(
                self.users[1], "GET", "/movements/subscriptions"
            )  # change into self.client.get
            # Check that get_subscriptions has been called
