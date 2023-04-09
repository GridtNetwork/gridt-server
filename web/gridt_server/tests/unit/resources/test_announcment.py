from unittest import skip
from unittest.mock import patch
from gridt_server.tests.base_test import BaseTest


class AnnouncementsTest(BaseTest):
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
        "gridt_server.resources.announcement.get_announcements",
        return_value=mock_results_query
    )
    def test_get_announcements(self, mock_get_announcements):
        with self.app_context():
            response = self.send_get_announcements(self.movement_id, self.user_id)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json(), self.mock_results_query)

        mock_get_announcements.assert_called_once_with(self.movement_id)

    @patch("gridt_server.resources.announcement.create_announcement")
    def test_post_announcement(self, mock_post_announcement):
        with self.app_context():
            new_announcement_json = {
                "message": self.message,
                "poster": self.user_id,
                "movement_id": self.movement_id
            }

            response = self.client.post(f"/movements/12/announcements", json=new_announcement_json,
                                        headers={"Authorization": self.obtain_token_header(self.user_id)})

            self.assertEqual(response.status_code, 201)
            self.assertEqual(
                response.get_json(), {"message": "Successfully created announcement."}
            )

        mock_post_announcement.assert_called_once_with(
            self.message, self.user_id, self.movement_id
        )

    def send_update_announcement_request(self, body, user_id, announcement_id):
        response = self.client.put(
            f"/movements/{self.movement_id}/announcements/{self.announcement_id}",
            headers={"Authorization": self.obtain_token_header(user_id)},
            json=body
        )
        return response

    @patch("gridt_server.resources.announcement.update_announcement")
    def test_update_announcement(self, mock_updated_announcement):
        body = {
            "message": "new message"
        }

        with self.app_context():
            response = self.send_update_announcement_request(body, self.user_id, self.announcement_id)
            self.assertEqual(response.status_code, 201)
            expected = {"message": "Announcement successfully updated."}
            self.assertEqual(response.get_json(), expected)

        mock_updated_announcement.assert_called_once_with("new message", self.announcement_id, self.user_id)

    def send_delete_announcement(self, user_id):
        response = self.client.delete(
            f"/movements/{self.movement_id}/announcements/{self.announcement_id}",
            headers={"Authorization": self.obtain_token_header(user_id)}
        )
        return response

    @patch("gridt_server.resources.announcement.delete_announcement")
    def test_delete(self, mock_delete_announcement):
        with self.app_context():
            response = self.send_delete_announcement(self.user_id)
            self.assertEqual(response.status_code, 201)
            expected = {"message": "Announcement successfully deleted."}
            self.assertEqual(response.get_json(), expected)

        mock_delete_announcement.assert_called_once_with(self.announcement_id, self.user_id)
