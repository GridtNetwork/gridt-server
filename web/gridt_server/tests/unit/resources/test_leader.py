from gridt_server.tests.base_test import BaseTest

from unittest import mock


class SwapTest(BaseTest):
    u_id = 42
    l_id = 5
    m_id = 1

    def send_request(self, user_id, leader_id, movement_id):
        response = self.client.post(
            f"/movements/{movement_id}/leader/{leader_id}",
            headers={"Authorization": self.obtain_token_header(user_id)},
        )
        return response

    @mock.patch(
        "gridt_server.resources.leader.swap_leader",
        return_value={"leader": "profile"}
    )
    @mock.patch("gridt_server.schemas.movement_exists", return_value=True)
    @mock.patch("gridt_server.schemas.is_subscribed", return_value=True)
    @mock.patch("gridt_server.schemas.user_exists", return_value=True)
    @mock.patch("gridt_server.schemas.follows_leader", return_value=True)
    def test_swap_leader(
        self,
        mock_follows,
        mock_user_exists,
        mock_is_subscribed,
        mock_movement_exists,
        mock_swap_leader
    ):
        with self.app_context():
            response = self.send_request(self.u_id, self.l_id, self.m_id)
            self.assertEqual(response.status_code, 200)
            self.assertDictEqual(
                response.get_json(),
                {"leader": "profile"}
            )

        mock_follows.assert_called_once_with(self.u_id, self.m_id, self.l_id)
        mock_user_exists.assert_called_once_with(self.l_id)
        mock_is_subscribed.assert_called_once_with(self.u_id, self.m_id)
        mock_movement_exists.assert_called_once_with(self.m_id)
        mock_swap_leader.assert_called_once_with(
            follower_id=self.u_id, movement_id=self.m_id, leader_id=self.l_id
        )

    @mock.patch("gridt_server.resources.leader.swap_leader")
    @mock.patch("gridt_server.schemas.movement_exists", return_value=False)
    def test_swap_leader_movement_nonexistant(
        self,
        mock_movement_exists,
        mock_swap_leader
    ):
        with self.app_context():
            response = self.send_request(self.u_id, self.l_id, self.m_id)
            self.assertEqual(response.status_code, 400)
            self.assertEqual(
                response.get_json(),
                {"message": "movement_id: No movement found for that id."},
            )

        mock_movement_exists.assert_called_once_with(self.m_id)
        mock_swap_leader.assert_not_called()

    @mock.patch("gridt_server.resources.leader.swap_leader")
    @mock.patch("gridt_server.schemas.movement_exists", return_value=True)
    @mock.patch("gridt_server.schemas.is_subscribed", return_value=False)
    def test_swap_leader_movement_not_subscribed(
        self,
        mock_is_subscribed,
        mock_movement_exists,
        mock_swap_leader
    ):
        expected_error = "_schema: User is not subscribed to this movement."

        with self.app_context():
            response = self.send_request(self.u_id, self.l_id, self.m_id)
            self.assertEqual(response.status_code, 400)
            self.assertEqual(
                response.get_json(),
                {"message": expected_error},
            )

        mock_is_subscribed.assert_called_once_with(self.u_id, self.m_id)
        mock_movement_exists.assert_called_once_with(self.m_id)
        mock_swap_leader.assert_not_called()

    @mock.patch("gridt_server.resources.leader.swap_leader")
    @mock.patch("gridt_server.schemas.movement_exists", return_value=True)
    @mock.patch("gridt_server.schemas.is_subscribed", return_value=True)
    @mock.patch("gridt_server.schemas.user_exists", return_value=True)
    @mock.patch("gridt_server.schemas.follows_leader", return_value=False)
    def test_swap_leader_not_leader(
        self,
        mock_follows,
        mock_user_exists,
        mock_is_subscribed,
        mock_movement_exists,
        mock_swap_leader
    ):
        with self.app_context():
            response = self.send_request(self.u_id, self.l_id, self.m_id)
            self.assertEqual(response.status_code, 400)
            self.assertEqual(
                response.get_json(),
                {"message": "_schema: User is not following this leader."},
            )

        mock_follows.assert_called_once_with(self.u_id, self.m_id, self.l_id)
        mock_user_exists.assert_called_once_with(self.l_id)
        mock_is_subscribed.assert_called_once_with(self.u_id, self.m_id)
        mock_movement_exists.assert_called_once_with(self.m_id)
        mock_swap_leader.assert_not_called()


class LeaderProfileTest(BaseTest):
    @mock.patch(
        "gridt_server.resources.leader.get_leader",
        return_value={"leader": "profile"}
    )
    @mock.patch("gridt_server.schemas.movement_exists", return_value=True)
    @mock.patch("gridt_server.schemas.is_subscribed", return_value=True)
    @mock.patch("gridt_server.schemas.user_exists", return_value=True)
    @mock.patch("gridt_server.schemas.follows_leader", return_value=True)
    def test_get_leader_profile(
        self,
        mock_follows,
        mock_user_exists,
        mock_is_subscribed,
        mock_movement_exists,
        mock_get_leader
    ):
        user_id = 1
        leader_id = 2
        movement_id = 3

        with self.app_context():
            response = self.client.get(
                f"/movements/{movement_id}/leader/{leader_id}",
                headers={"Authorization": self.obtain_token_header(user_id)},
            )

            self.assertEqual(response.status_code, 200)
            self.assertDictEqual(
                response.get_json(),
                {"leader": "profile"}
            )

        mock_follows.assert_called_once_with(user_id, movement_id, leader_id)
        mock_user_exists.assert_called_once_with(leader_id)
        mock_is_subscribed.assert_called_once_with(user_id, movement_id)
        mock_movement_exists.assert_called_once_with(movement_id)
        mock_get_leader.assert_called_once_with(
            follower_id=user_id, movement_id=movement_id, leader_id=leader_id
        )
