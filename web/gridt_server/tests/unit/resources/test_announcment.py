from unittest.mock import patch
from gridt_server.tests.base_test import BaseTest
from gridt.exc import UserNotAdmin


class AnnouncementsTest(BaseTest):
    resource_path = 'gridt_server.resources.announcement'

    user_id = 42
    movement_id = 12
    announcement_id = 1
    message = "new message"
    mock_announcement1 = {
        "id": 1,
        "message": "This is the announcement 1",
        "poster": 42,
        "movement_id": 12,
    }

    mock_results_query = [
        mock_announcement1
    ]

    def send_get_announcements(self, movement_id, user_id):
        response = self.client.get(
            f"/movements/{movement_id}/announcements",
            headers={"Authorization": self.obtain_token_header(user_id)}
        )
        return response

    @patch(
        f"{resource_path}.get_announcements",
        return_value=mock_results_query
    )
    def test_get_announcements(self, mock_get_announcements):
        with self.app_context():
            response = self.send_get_announcements(self.movement_id, self.user_id)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json(), self.mock_results_query)

        mock_get_announcements.assert_called_once_with(self.movement_id)

    @patch(f"{resource_path}.create_announcement")
    def test_post_announcement(self, mock_post_announcement):
        body = {
            "message": self.message,
            "poster": self.user_id,
            "movement_id": self.movement_id
        }
        expected = {"message": "Successfully created announcement."}
        with self.app_context():
            token = self.obtain_token_header(self.user_id)
            response = self.client.post(
                f"/movements/{self.movement_id}/announcements",
                json=body,
                headers={"Authorization": token}
            )

            self.assertEqual(response.status_code, 201)
            self.assertEqual(response.get_json(), expected)

        mock_post_announcement.assert_called_once_with(
            message=self.message,
            user_id=self.user_id,
            movement_id=self.movement_id
        )

    @patch(f"{resource_path}.create_announcement", side_effect=UserNotAdmin)
    def test_post_announcement_non_admin(self, mock_post_announcement):
        body = {
            "message": self.message,
            "poster": self.user_id,
            "movement_id": self.movement_id
        }
        expected_message = "Insufficient privileges to create an announcement."
        with self.app_context():
            token = self.obtain_token_header(self.user_id)
            response = self.client.post(
                f"/movements/{self.movement_id}/announcements",
                json=body,
                headers={"Authorization": token}
            )

            self.assertEqual(response.status_code, 403)
            self.assertEqual(response.get_json()['message'], expected_message)

        mock_post_announcement.assert_called_once_with(
            message=self.message,
            user_id=self.user_id,
            movement_id=self.movement_id
        )

    def send_update_announcement_request(self, body, user_id, announcement_id):
        response = self.client.put(
            f"/movements/{self.movement_id}/announcements/{announcement_id}",
            headers={"Authorization": self.obtain_token_header(user_id)},
            json=body
        )
        return response

    @patch(f"{resource_path}.update_announcement")
    def test_update_announcement(self, mock_updated_announcement):
        body = {"message": "new message"}

        with self.app_context():
            response = self.send_update_announcement_request(
                body, self.user_id, self.announcement_id
            )
            self.assertEqual(response.status_code, 201)
            expected = {"message": "Announcement successfully updated."}
            self.assertEqual(response.get_json(), expected)

        mock_updated_announcement.assert_called_once_with(
            message="new message",
            announcement_id=self.announcement_id,
            user_id=self.user_id
        )

    @patch(f"{resource_path}.update_announcement", side_effect=UserNotAdmin)
    def test_update_announcement_non_admin(self, mock_updated_announcement):
        body = {"message": "new message"}
        expected_message = "Insufficient privileges to update an announcement."

        with self.app_context():
            response = self.send_update_announcement_request(
                body, self.user_id, self.announcement_id
            )
            self.assertEqual(response.status_code, 403)
            self.assertEqual(response.get_json()['message'], expected_message)

        mock_updated_announcement.assert_called_once_with(
            message="new message",
            announcement_id=self.announcement_id,
            user_id=self.user_id
        )

    def send_delete_announcement(self, user_id):
        response = self.client.delete(
            f"/movements/{self.movement_id}/announcements/{self.announcement_id}",
            headers={"Authorization": self.obtain_token_header(user_id)}
        )
        return response

    @patch(f"{resource_path}.delete_announcement")
    def test_delete(self, mock_delete):
        with self.app_context():
            response = self.send_delete_announcement(self.user_id)
            self.assertEqual(response.status_code, 201)
            expected = {"message": "Announcement successfully deleted."}
            self.assertEqual(response.get_json(), expected)

        mock_delete.assert_called_once_with(self.announcement_id, self.user_id)

    @patch(f"{resource_path}.delete_announcement", side_effect=UserNotAdmin())
    def test_delete_non_admin(self, mock_delete):
        expected_message = "Insufficient privileges to delete an announcement."
        with self.app_context():
            response = self.send_delete_announcement(self.user_id)
            self.assertEqual(response.status_code, 403)
            self.assertEqual(response.get_json()['message'], expected_message)

        mock_delete.assert_called_once_with(self.announcement_id, self.user_id)
