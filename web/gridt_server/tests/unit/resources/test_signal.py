from unittest.mock import patch

from gridt_server.tests.base_test import BaseTest


class SignalTest(BaseTest):
    message = "Hello Movement!"

    def send_request(self, user_id, message):
        with self.app_context():
            response = self.client.post(
                "/movements/1/signal",
                headers={"Authorization": self.obtain_token_header(user_id)},
                json={"message": message}
            )
        return response

    @patch("gridt_server.resources.movements.send_signal")
    @patch("gridt_server.schemas.movement_exists", return_value=True)
    @patch("gridt_server.schemas.user_exists", return_value=True)
    @patch("gridt_server.schemas.is_subscribed", return_value=True)
    def test_send_signal(
        self,
        mock_is_subscribed,
        mock_user_exists,
        mock_movement_exists,
        mock_send_signal,
    ):
        response = self.send_request(42, self.message)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.get_json()["message"],
            "Successfully created signal."
        )

        mock_movement_exists.assert_called_once_with(1)
        mock_user_exists.assert_called_once_with(42)
        mock_is_subscribed.assert_called_once_with(42, 1)
        mock_send_signal.assert_called_once_with(42, 1, self.message)

    @patch("gridt_server.resources.movements.send_signal")
    @patch("gridt_server.schemas.movement_exists", return_value=False)
    @patch("gridt_server.schemas.user_exists", return_value=True)
    @patch("gridt_server.schemas.is_subscribed", return_value=True)
    def test_send_signal_no_movement(
        self,
        mock_is_subscribed,
        mock_user_exists,
        mock_movement_exists,
        mock_send_signal,
    ):
        response = self.send_request(42, self.message)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.get_json()["message"],
            "movement_id: No movement found for that id."
        )

        mock_movement_exists.assert_called_once_with(1)
        mock_send_signal.assert_not_called()

    @patch("gridt_server.resources.movements.send_signal")
    @patch("gridt_server.schemas.movement_exists", return_value=True)
    @patch("gridt_server.schemas.user_exists", return_value=True)
    @patch("gridt_server.schemas.is_subscribed", return_value=False)
    def test_send_signal_not_subscribed(
        self,
        mock_is_subscribed,
        mock_user_exists,
        mock_movement_exists,
        mock_send_signal,
    ):
        response = self.send_request(42, self.message)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.get_json()["message"],
            "_schema: User not subscribed to movement"
        )

        mock_is_subscribed.is_called_once_with(42, 1)
        mock_send_signal.assert_not_called()
