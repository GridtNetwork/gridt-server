"""Unittests for the get network data endpoint."""

from unittest.mock import patch

from gridt_server.tests.base_test import BaseTest


class NetworkResourceTest(BaseTest):
    """Unittests for the validation of GETs to: /movements/<id>/data."""

    resource_path = 'gridt_server.resources.network'
    schema_path = 'gridt_server.schemas'
    user_id = 42
    movement_id = 1

    def __send_data_request(self):
        """Send the get request to the /movements/<id>/data endpoint."""
        response = self.client.get(
            f'/movements/{self.movement_id}/data',
            headers={"Authorization": self.obtain_token_header(self.user_id)}
        )
        return response

    @patch(f"{resource_path}.get_network_data", return_value="data")
    @patch(f'{schema_path}.movement_exists', return_value=True)
    def test_get_data_valid(self, mock_movement_exists, mock_get_data):
        """Test get movement data when movement exists."""
        with self.app_context():
            response = self.__send_data_request()
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json(), "data")
        mock_movement_exists.assert_called_once_with(self.movement_id)
        mock_get_data.assert_called_once_with(self.movement_id)

    @patch(f"{resource_path}.get_network_data")
    @patch(f'{schema_path}.movement_exists', return_value=False)
    def test_get_data_invalid(self, mock_movement_exists, mock_get_data):
        """Test get movement data when movement does not exists."""
        expected = {"message": "movement_id: No movement found for that id."}
        with self.app_context():
            response = self.__send_data_request()
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.get_json(), expected)
        mock_movement_exists.assert_called_once_with(self.movement_id)
        mock_get_data.assert_not_called()
