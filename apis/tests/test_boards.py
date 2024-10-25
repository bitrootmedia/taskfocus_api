import uuid

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from core.models import User, Task, Board, BoardUser, Card, CardTask


class BoardTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username="user1")
        cls.user_2 = User.objects.create(username="user2")
        cls.user_3 = User.objects.create(username="user3")  # No Board access

        cls.task = Task.objects.create(
            owner=cls.user, title="Task 1", description="Task 1 Description"
        )

        cls.task_2 = Task.objects.create(
            owner=cls.user_2,
            title="Task 2",
            description="Task 2 Description",
        )

        cls.task_3 = Task.objects.create(
            owner=cls.user,
            title="Task 3",
            description="Task 3 Description",
        )

        cls.board = Board.objects.create(
            owner=cls.user,
            name="Board 1",
        )

        cls.board_2 = Board.objects.create(
            owner=cls.user_2,
            name="Board 2",
        )

        cls.board_3 = Board.objects.create(
            owner=cls.user_2,
            name="Board 3",
        )

        cls.board_user = BoardUser.objects.create(
            board=cls.board,
            user=cls.user_2,
        )

        cls.board_2_user = BoardUser.objects.create(
            board=cls.board_2,
            user=cls.user,
        )

        cls.card = Card.objects.create(
            board=cls.board,
            name="Card 1",
            position=0,
        )

        cls.card_task = CardTask.objects.create(
            card=cls.card,
            task=cls.task,
            position=0,
        )

        cls.card_task_2 = CardTask.objects.create(
            card=cls.card,
            task=cls.task_2,
            position=1,
        )

        cls.card_2 = Card.objects.create(
            board=cls.board,
            name="Card 2",
            position=1,
        )

        cls.card_task_3 = CardTask.objects.create(
            card=cls.card_2,
            task=cls.task_3,
            position=0,
        )

    def test_board_list(self):
        self.client.force_login(user=self.user)
        response = self.client.get(reverse("board_list"))
        board_ids = [x["id"] for x in response.json()["results"]]

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn(str(self.board.id), board_ids)
        self.assertIn(str(self.board_2.id), board_ids)
        self.assertNotIn(str(self.board_3.id), board_ids)

    def test_board_detail_get_not_owner(self):
        self.client.force_login(user=self.user_2)  # not owner
        response = self.client.get(
            reverse("board_detail", kwargs={"pk": self.board.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_board_detail_edit_not_owner(self):
        self.client.force_login(user=self.user_2)
        response = self.client.put(
            reverse("board_detail", kwargs={"pk": self.board.id})
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_board_detail_edit(self):
        self.client.force_login(user=self.user)
        response = self.client.put(
            reverse("board_detail", kwargs={"pk": self.board.id}),
            {"name": "Board 1 Name Updated", "owner": self.user.id},
        )

        self.board.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.board.name, "Board 1 Name Updated")

    def test_board_detail_delete_not_owner(self):
        self.client.force_login(user=self.user_2)
        response = self.client.delete(
            reverse("board_detail", kwargs={"pk": self.board.id})
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_board_detail_delete(self):
        self.client.force_login(user=self.user)
        response = self.client.delete(
            reverse("board_detail", kwargs={"pk": self.board.id})
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    # ---- BoardUser Tests ----

    def test_board_user_get_users(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("board_users", kwargs={"board_id": self.board.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_board_users_get_no_users(self):
        self.client.force_login(self.user_2)
        response = self.client.get(
            reverse("board_users", kwargs={"board_id": self.board_3.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_board_user_create_not_owner(self):
        self.client.force_login(self.user_2)
        response = self.client.post(
            reverse("board_users", kwargs={"board_id": self.board.id})
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_board_user_create(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("board_users", kwargs={"board_id": self.board.id}),
            {"user": self.user_3.id},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_board_user_create_already_exists(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("board_users", kwargs={"board_id": self.board.id}),
            {"user": self.user_2.id},
        )
        self.assertEqual(response.status_code, status.HTTP_304_NOT_MODIFIED)

    def test_board_user_create_invalid_user_id(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("board_users", kwargs={"board_id": self.board.id}),
            {"user": uuid.uuid4()},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_board_user_list_no_access(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("board_users", kwargs={"board_id": self.board_3.id})
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_board_user_delete_not_owner(self):
        self.client.force_login(self.user_2)
        response = self.client.delete(
            reverse("board_users", kwargs={"board_id": self.board.id})
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_board_user_delete(self):
        self.client.force_login(self.user)
        response = self.client.delete(
            reverse("board_users", kwargs={"board_id": self.board.id}),
            {"user": self.board_user.user.id},
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        with self.assertRaises(BoardUser.DoesNotExist):
            self.board_user.refresh_from_db()

    def test_board_user_delete_not_board_user(self):
        self.client.force_login(self.user)
        response = self.client.delete(
            reverse("board_users", kwargs={"board_id": self.board.id}),
            {"user": self.user_3.id},
        )
        self.assertEqual(response.status_code, status.HTTP_304_NOT_MODIFIED)

    def test_board_user_delete_invalid_user_id(self):
        self.client.force_login(self.user)
        response = self.client.delete(
            reverse("board_users", kwargs={"board_id": self.board.id}),
            {"user": uuid.uuid4()},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ---- Card Tests ----

    def test_card_create(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("card_create"),
            {
                "board": self.board.id,
                "name": "New Card",
                "position": 0,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_card_create_no_access_to_board(self):
        self.client.force_login(self.user_3)
        response = self.client.post(
            reverse("card_create"),
            {
                "board": self.board.id,
                "name": "New Card",
                "position": 0,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_card_edit(self):
        self.client.force_login(self.user)
        response = self.client.put(
            reverse("card_detail", kwargs={"pk": self.card.id}),
            {"name": "New Name", "board": self.card.board.id},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.card.refresh_from_db()
        self.assertEqual(self.card.name, "New Name")

    def test_card_delete(self):
        self.client.force_login(self.user)
        response = self.client.delete(
            reverse("card_detail", kwargs={"pk": self.card.id})
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_card_move(self):
        self.client.force_login(self.user)
        response = self.client.put(
            reverse("card_move"), {"card": self.card.id, "position": 1}
        )
        self.card.refresh_from_db()
        self.card_2.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.card.position, 1)
        self.assertEqual(self.card_2.position, 0)

    # ---- Card Task Tests ----

    def test_card_move_same_position(self):
        self.client.force_login(self.user)
        response = self.client.put(
            reverse("card_move"), {"card": self.card.id, "position": 0}
        )
        self.assertEqual(response.status_code, status.HTTP_304_NOT_MODIFIED)

    def test_card_task_create(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("card_task_create"),
            {"task": self.task_3.id, "card": self.card_2.id, "position": 0},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_card_task_create_no_board_access(self):
        self.client.force_login(self.user_3)
        response = self.client.post(
            reverse("card_task_create"),
            {"task": self.task_3.id, "card": self.card_2.id, "position": 0},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_card_task_delete(self):
        self.client.force_login(self.user)
        response = self.client.delete(
            reverse("card_task_detail", kwargs={"pk": self.card_task_2.id})
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        with self.assertRaises(CardTask.DoesNotExist):
            self.card_task_2.refresh_from_db()

    def test_card_task_move_same_card(self):
        self.client.force_login(self.user)
        response = self.client.put(
            reverse("card_task_move"),
            {
                "task": self.card_task.id,
                "card": self.card_task.card.id,
                "position": 1,
            },
        )
        self.card_task.refresh_from_db()
        self.card_task_2.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.card_task.position, 1)
        self.assertEqual(self.card_task_2.position, 0)

    def test_card_task_move_different_card(self):
        self.client.force_login(self.user)
        response = self.client.put(
            reverse("card_task_move"),
            {"task": self.card_task.id, "card": self.card_2.id, "position": 0},
        )
        self.card_task.refresh_from_db()
        self.card_task_2.refresh_from_db()
        self.card_task_3.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # new card and new position
        self.assertEqual(self.card_task.card.id, self.card_2.id)
        self.assertEqual(self.card_task.position, 0)
        # previous 0 in new card is now 1
        self.assertEqual(self.card_task_3.position, 1)
        # previous 1 in old card is now 0
        self.assertEqual(self.card_task_2.position, 0)
