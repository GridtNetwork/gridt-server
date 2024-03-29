from unittest import skip
from unittest.mock import patch

from gridt_server.tests.base_test import BaseTest
from gridt.exc import UserNotAdmin


class MovementsTest(BaseTest):
    resource_path = 'gridt_server.resources.movements'
    schema_path = 'gridt_server.schemas'

    user_id = 42
    mock_movement = {
        "id": 1,
        "description": "",
        "interval": "twice daily",
        "last_signal_sent": None,
        "leaders": [{"id": 5, "last_signal": None, "username": "test1"}],
        "name": "test1",
        "short_description": "Hello",
        "subscribed": True,
    }
    mock_movement_not_subscribed = {
        "id": 2,
        "description": "",
        "interval": "daily",
        "name": "test2",
        "short_description": "Hello",
        "subscribed": False,
    }
    mock_query_results = [
        mock_movement,
        mock_movement_not_subscribed
    ]

    def send_get_movements(self, user_id):
        response = self.client.get(
            "/movements",
            headers={"Authorization": self.obtain_token_header(user_id)}
        )
        return response

    def send_add_movement(self, user_id, body):
        response = self.client.post(
            "/movements",
            headers={"Authorization": self.obtain_token_header(user_id)},
            json=body
        )
        return response

    @patch(
        f"{resource_path}.get_all_movements",
        return_value=mock_query_results
    )
    def test_get_movements(self, mock_get_all_movements):
        with self.app_context():
            response = self.send_get_movements(self.user_id)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json(), self.mock_query_results)

        mock_get_all_movements.assert_called_once_with(self.user_id)

    @patch(f"{resource_path}.new_movement_by_user")
    @patch(f"{schema_path}.movement_name_exists", return_value=True)
    def test_post_name_exists(self, mock_name_exists, mock_new_movement):
        body = {
            "name": "movement",
            "short_description": "testing post request",
            "interval": "daily"
        }
        expect_message = "name: Movement name already in use."

        with self.app_context():
            response = self.send_add_movement(self.user_id, body)
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.get_json()["message"], expect_message)

        mock_name_exists.assert_called_once_with(body["name"])
        mock_new_movement.assert_not_called()

    @patch(f"{resource_path}.new_movement_by_user")
    @patch(f"{schema_path}.movement_name_exists", return_value=False)
    def test_interval_empty(self, mock_name_exists, mock_new_movement):
        body = {
            "name": "movement",
            "short_description": "testing post request",
        }
        expect_message = "interval: Missing data for required field."

        with self.app_context():
            response = self.send_add_movement(self.user_id, body)
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.get_json()["message"], expect_message)

        mock_name_exists.assert_called_once_with(body["name"])
        mock_new_movement.assert_not_called()

    @skip
    def test_name_empty(self):
        pass

    @patch(f"{resource_path}.new_movement_by_user")
    @patch(f"{schema_path}.movement_name_exists", return_value=False)
    def test_post_successful(self, mock_name_exists, mock_new_movement):
        body = {
            "name": "movement",
            "short_description": "testing post request",
            "interval": "daily"
        }
        expect_message = "Successfully created movement."

        with self.app_context():
            response = self.send_add_movement(self.user_id, body)
            self.assertEqual(response.status_code, 201)
            self.assertEqual(response.get_json()["message"], expect_message)

        mock_name_exists.assert_called_once_with(body["name"])
        mock_new_movement.assert_called_once_with(
            user_id=self.user_id,
            name=body['name'],
            interval=body["interval"],
            short_description=body["short_description"],
            description=None
        )

    @patch(f"{resource_path}.new_movement_by_user", side_effect=UserNotAdmin)
    @patch(f"{schema_path}.movement_name_exists", return_value=False)
    def test_post_non_admin(self, mock_name_exists, mock_new_movement):
        body = {
            "name": "movement",
            "short_description": "testing post request",
            "interval": "daily"
        }
        expect_message = "Insufficient privileges to create a movement."

        with self.app_context():
            response = self.send_add_movement(self.user_id, body)
            self.assertEqual(response.status_code, 403)
            self.assertEqual(response.get_json()["message"], expect_message)

        mock_name_exists.assert_called_once_with(body["name"])
        mock_new_movement.assert_called_once_with(
            user_id=self.user_id,
            name=body['name'],
            interval=body["interval"],
            short_description=body["short_description"],
            description=None
        )

    def send_get_movement(self, user_id, movement_id):
        response = self.client.get(
            f"/movements/{movement_id}",
            headers={"Authorization": self.obtain_token_header(user_id)}
        )
        return response

    @patch(
        f'{resource_path}.get_movement',
        return_value=mock_movement
    )
    @patch(f'{schema_path}.movement_exists', return_value=True)
    def test_single_movement_by_id(
        self,
        mock_movement_exists,
        mock_get_movement
    ):
        movement_id = self.mock_movement['id']

        with self.app_context():
            response = self.send_get_movement(self.user_id, movement_id)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json(), self.mock_movement)

        mock_movement_exists.assert_called_once_with(movement_id)
        mock_get_movement.assert_called_once_with(movement_id, self.user_id)

    @patch(
        f'{resource_path}.get_movement',
        return_value=mock_movement
    )
    @patch(f'{schema_path}.movement_exists', return_value=False)
    def test_single_movement_nonexisting(
        self,
        mock_movement_exists,
        mock_get_movement
    ):
        movement_id = self.mock_movement['id']
        expect_message = "movement_id: No movement found for that id."

        with self.app_context():
            response = self.send_get_movement(self.user_id, movement_id)
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.get_json()['message'], expect_message)

        mock_movement_exists.assert_called_once_with(movement_id)
        mock_get_movement.assert_not_called()


class SubscribeTest(BaseTest):
    resource_path = 'gridt_server.resources.movements'
    schema_path = 'gridt_server.schemas'

    user_id = 42
    movement_id = 1024

    def send_subscribe(self, user_id, movement_id):
        response = self.client.put(
            f'/movements/{movement_id}/subscriber',
            headers={'Authorization': self.obtain_token_header(user_id)}
        )
        return response

    def send_unsubscribe(self, user_id, movement_id):
        response = self.client.delete(
            f'/movements/{movement_id}/subscriber',
            headers={'Authorization': self.obtain_token_header(user_id)}
        )
        return response

    @patch(f'{resource_path}.new_subscription')
    @patch(f'{resource_path}.is_subscribed', return_value=False)
    @patch(f'{schema_path}.movement_exists', return_value=True)
    def test_subscribe(
        self, mock_movement_exists, mock_is_subscribed, mock_new_subscription
    ):
        expected = {"message": "Successfully subscribed to this movement."}
        with self.app_context():
            response = self.send_subscribe(self.user_id, self.movement_id)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json(), expected)

        mock_movement_exists.assert_called_once_with(self.movement_id)
        mock_is_subscribed.assert_called_once_with(
            self.user_id, self.movement_id
        )
        mock_new_subscription.assert_called_once_with(
            self.user_id, self.movement_id
        )

    @patch(f'{resource_path}.new_subscription')
    @patch(f'{resource_path}.is_subscribed', return_value=False)
    @patch(f'{schema_path}.movement_exists', return_value=False)
    def test_subscribe_nonexisting_movement(
        self, mock_movement_exists, mock_is_subscribed, mock_new_subscription
    ):
        expected = {"message": "movement_id: No movement found for that id."}
        with self.app_context():
            response = self.send_subscribe(self.user_id, self.movement_id)
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.get_json(), expected)

        mock_movement_exists.assert_called_once_with(self.movement_id)
        mock_is_subscribed.assert_not_called()
        mock_new_subscription.assert_not_called()

    @patch(f'{resource_path}.new_subscription')
    @patch(f'{resource_path}.is_subscribed', return_value=True)
    @patch(f'{schema_path}.movement_exists', return_value=True)
    def test_already_subscribed(
        self, mock_movement_exists, mock_is_subscribed, mock_new_subscription
    ):
        expected = {"message": "Successfully subscribed to this movement."}
        with self.app_context():
            response = self.send_subscribe(self.user_id, self.movement_id)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json(), expected)

        mock_movement_exists.assert_called_once_with(self.movement_id)
        mock_is_subscribed.assert_called_once_with(
            self.user_id, self.movement_id
        )
        mock_new_subscription.assert_not_called()

    @patch(f'{resource_path}.remove_subscription')
    @patch(f'{resource_path}.is_subscribed', return_value=True)
    @patch(f'{schema_path}.movement_exists', return_value=True)
    def test_unsubscribe(
        self,
        mock_movement_exists,
        mock_is_subscribed,
        mock_remove_subscription
    ):
        expected = {"message": "Successfully unsubscribed from this movement."}
        with self.app_context():
            response = self.send_unsubscribe(self.user_id, self.movement_id)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json(), expected)

        mock_movement_exists.assert_called_once_with(self.movement_id)
        mock_is_subscribed.assert_called_once_with(
            self.user_id, self.movement_id
        )
        mock_remove_subscription.assert_called_once_with(
            self.user_id, self.movement_id
        )

    @patch(f'{resource_path}.remove_subscription')
    @patch(f'{schema_path}.movement_exists', return_value=False)
    def test_unsubscribe_nonexisting_movement(
        self, mock_movement_exists, mock_remove_subscription
    ):
        expected = {"message": "movement_id: No movement found for that id."}
        with self.app_context():
            response = self.send_unsubscribe(self.user_id, self.movement_id)
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.get_json(), expected)

        mock_movement_exists.assert_called_once_with(self.movement_id)
        mock_remove_subscription.assert_not_called()


class NewSignalTest(BaseTest):
    resource_path = 'gridt_server.resources.movements'
    schema_path = 'gridt_server.schemas'

    user_id = 42
    movement_id = 1
    not_movement_id = 100
    message = "Hello Movement!"

    def send_request(self, user_id, movement_id, message):
        response = self.client.post(
            f'movements/{movement_id}/signal',
            headers={'Authorization': self.obtain_token_header(user_id)},
            json={'message': message}
        )
        return response

    @patch(f"{resource_path}.send_signal")
    @patch(f"{schema_path}.movement_exists", return_value=True)
    @patch(f"{schema_path}.user_exists", return_value=True)
    @patch(f"{schema_path}.is_subscribed", return_value=True)
    def test_create_new_signal(
        self,
        mock_is_sub,
        mock_user_exists,
        mock_movement_exists,
        mock_send_signal
    ):
        expected = {"message": "Successfully created signal."}
        with self.app_context():
            response = self.send_request(
                self.user_id, self.movement_id, self.message
            )
            self.assertEqual(response.status_code, 201)
            self.assertEqual(response.get_json(), expected)

        mock_movement_exists.assert_called_once_with(self.movement_id)
        mock_user_exists.assert_called_once_with(self.user_id)
        mock_is_sub.assert_called_once_with(self.user_id, self.movement_id)
        mock_send_signal.assert_called_once_with(
            self.user_id, self.movement_id, self.message
        )

    @patch(f"{resource_path}.send_signal")
    @patch(f"{schema_path}.movement_exists", return_value=False)
    @patch(f"{schema_path}.user_exists", return_value=True)
    @patch(f"{schema_path}.is_subscribed", side_effect=False)
    def test_signal_nonexisting_movement(
        self,
        mock_is_subscribed,
        mock_user_exists,
        mock_movement_exists,
        mock_send_signal
    ):
        expected = {'message': "movement_id: No movement found for that id."}
        with self.app_context():
            response = self.send_request(
                self.user_id, self.not_movement_id, self.message
            )
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.get_json(), expected)

        mock_movement_exists.assert_called_once_with(self.not_movement_id)
        mock_user_exists.assert_called_once_with(self.user_id)
        mock_is_subscribed.assert_not_called()
        mock_send_signal.assert_not_called()

    @patch(f"{resource_path}.send_signal")
    @patch(f"{schema_path}.movement_exists", return_value=True)
    @patch(f"{schema_path}.user_exists", return_value=True)
    @patch(f"{schema_path}.is_subscribed", return_value=False)
    def test_movement_not_subscribed(
        self,
        mock_is_sub,
        mock_user_exists,
        mock_movement_exists,
        mock_send_signal
    ):
        expected = {'message': "_schema: User not subscribed to movement"}
        with self.app_context():
            response = self.send_request(
                self.user_id, self.movement_id, self.message
            )
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.get_json(), expected)

        mock_movement_exists.assert_called_once_with(self.movement_id)
        mock_user_exists.assert_called_once_with(self.user_id)
        mock_is_sub.assert_called_once_with(self.user_id, self.movement_id)
        mock_send_signal.assert_not_called()


class SubscriptionsResourceTest(BaseTest):
    resource_path = 'gridt_server.resources.movements'
    schema_path = 'gridt_server.schemas'

    user_id = 42
    movement = {
        "id": 1,
        "description": "",
        "interval": "twice daily",
        "last_signal_sent": None,
        "leaders": [{"id": 5, "last_signal": None, "username": "test1"}],
        "name": "test1",
        "short_description": "Hello",
        "subscribed": True,
    }

    @patch(
        f'{resource_path}.get_subscriptions',
        return_value=[movement]
    )
    def test_get_subscriptions(self, mock_get_subscriptions):
        with self.app_context():
            token = self.obtain_token_header(self.user_id)
            response = self.client.get(
                '/movements/subscriptions',
                headers={'Authorization': token}
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json(), [self.movement])

        mock_get_subscriptions.assert_called_once_with(self.user_id)
