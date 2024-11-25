import uuid

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from core.models import User, Task, Board, BoardUser, Card, CardItem, Project


class BoardTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username="user1")
        cls.user_2 = User.objects.create(username="user2")
        cls.user_3 = User.objects.create(username="user3")  # No Board access
        cls.user_4 = User.objects.create(username="user4")  # No Board access

        cls.project = Project.objects.create(title="project1", owner=cls.user)

        cls.task = Task.objects.create(
            owner=cls.user,
            title="Task 1",
            description="Task 1 Description",
            project=cls.project,
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

        cls.board_user_4 = BoardUser.objects.create(
            board=cls.board, user=cls.user_4
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

        cls.card_item = CardItem.objects.create(
            card=cls.card,
            task=cls.task,
            position=0,
        )

        cls.card_item_2 = CardItem.objects.create(
            card=cls.card,
            task=cls.task_2,
            position=1,
        )

        cls.card_2 = Card.objects.create(
            board=cls.board,
            name="Card 2",
            position=1,
        )

        cls.card_item_3 = CardItem.objects.create(
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

    def test_board_list_search(self):
        self.client.force_login(user=self.user)
        response = self.client.get(
            reverse("board_list") + f"?name={self.board.name}"
        )
        board_ids = [x["id"] for x in response.json()["results"]]

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn(str(self.board.id), board_ids)
        self.assertNotIn(str(self.board_2.id), board_ids)
        self.assertNotIn(str(self.board_3.id), board_ids)

    def test_board_create(self):
        self.client.force_login(user=self.user)
        response = self.client.post(
            reverse("board_list"),
            data={"name": "NEW BOARD TEST", "owner": self.user.id},
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        board = Board.objects.get(name="NEW BOARD TEST")
        self.assertEqual(board.name, "NEW BOARD TEST")
        self.assertEqual(board.owner, self.user)

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

    def test_board_detail_edit_config(self):
        self.client.force_login(user=self.user)
        response = self.client.patch(
            reverse("board_detail", kwargs={"pk": self.board.id}),
            {"config": {"class": "bg-pink"}},
            format="json",
        )
        self.board.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.board.config, {"class": "bg-pink"})

    def test_board_detail_delete_not_owner(self):
        self.client.force_login(user=self.user_2)
        response = self.client.delete(
            reverse("board_detail", kwargs={"pk": self.board.id})
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_board_detail_delete_not_empty(self):
        self.client.force_login(user=self.user)
        response = self.client.delete(
            reverse("board_detail", kwargs={"pk": self.board.id})
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            "Cannot remove a board that contains items",
            response.json()["detail"],
        )

    def test_board_detail_delete(self):
        # Delete all items from the board
        CardItem.objects.filter(card__board=self.board).delete()

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

    def test_card_edit_config(self):
        self.client.force_login(self.user)
        response = self.client.patch(
            reverse("card_detail", kwargs={"pk": self.card.id}),
            {"config": {"class": "bg-pink"}},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.card.refresh_from_db()
        self.assertEqual(self.card.config, {"class": "bg-pink"})

    def test_card_delete_not_empty(self):
        self.client.force_login(self.user)
        response = self.client.delete(
            reverse("card_detail", kwargs={"pk": self.card.id})
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            "Cannot remove a card that contains items",
            response.json()["detail"],
        )

    def test_card_delete(self):
        # Delete all items from the card
        CardItem.objects.filter(card=self.card).delete()

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

    def test_card_move_same_position(self):
        self.client.force_login(self.user)
        response = self.client.put(
            reverse("card_move"), {"card": self.card.id, "position": 0}
        )
        self.assertEqual(response.status_code, status.HTTP_304_NOT_MODIFIED)

    # ---- Card Item Tests ----

    def test_card_item_create_task_only(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("card_item_create"),
            {"task": self.task_3.id, "card": self.card_2.id, "position": 0},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        item = CardItem.objects.get(id=response.json()["id"])
        self.assertEqual(item.task, self.task_3)

    def test_card_item_create_project_only(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("card_item_create"),
            {
                "project": self.project.id,
                "card": self.card_2.id,
                "position": 0,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        item = CardItem.objects.get(id=response.json()["id"])
        self.assertEqual(item.project, self.project)

    def test_card_item_create_comment_only(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("card_item_create"),
            {
                "comment": "Comment content",
                "card": self.card_2.id,
                "position": 0,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        item = CardItem.objects.get(id=response.json()["id"])
        self.assertEqual(item.comment, "Comment content")

    def test_card_item_create_mixed_data(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("card_item_create"),
            {
                "task": self.task.id,
                "project": self.project.id,
                "comment": "Comment content",
                "card": self.card_2.id,
                "position": 0,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        item = CardItem.objects.get(id=response.json()["id"])
        self.assertEqual(item.task, self.task)
        self.assertEqual(item.project, self.project)
        self.assertEqual(item.comment, "Comment content")

    def test_card_item_create_no_board_access(self):
        self.client.force_login(self.user_3)
        response = self.client.post(
            reverse("card_item_create"),
            {"task": self.task_3.id, "card": self.card_2.id, "position": 0},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_card_item_edit_config(self):
        self.client.force_login(self.user)
        response = self.client.patch(
            reverse("card_item_detail", kwargs={"pk": self.card_item.id}),
            {"config": {"class": "bg-pink"}},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.card_item.refresh_from_db()
        self.assertEqual(self.card_item.config, {"class": "bg-pink"})

    def test_card_item_delete(self):
        self.client.force_login(self.user)
        response = self.client.delete(
            reverse("card_item_detail", kwargs={"pk": self.card_item_2.id})
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        with self.assertRaises(CardItem.DoesNotExist):
            self.card_item_2.refresh_from_db()

    def test_card_item_move_same_card(self):
        self.client.force_login(self.user)
        response = self.client.put(
            reverse("card_item_move"),
            {
                "item": self.card_item.id,
                "card": self.card_item.card.id,
                "position": 1,
            },
        )
        self.card_item.refresh_from_db()
        self.card_item_2.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.card_item.position, 1)
        self.assertEqual(self.card_item_2.position, 0)

    def test_card_item_move_different_card(self):
        self.client.force_login(self.user)
        response = self.client.put(
            reverse("card_item_move"),
            {"item": self.card_item.id, "card": self.card_2.id, "position": 0},
        )
        self.card_item.refresh_from_db()
        self.card_item_2.refresh_from_db()
        self.card_item_3.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # new card and new position
        self.assertEqual(self.card_item.card.id, self.card_2.id)
        self.assertEqual(self.card_item.position, 0)
        # previous 0 in new card is now 1
        self.assertEqual(self.card_item_3.position, 1)
        # previous 1 in old card is now 0
        self.assertEqual(self.card_item_2.position, 0)

    # --- CardItem get_log_label tests ---

    def test_card_item_get_log_label_task(self):
        card_item = CardItem.objects.create(
            card=self.card,
            task=self.task,
        )
        label = card_item.get_log_label()
        self.assertEqual(label, f"Item ({self.task.title})")

    def test_card_item_get_log_label_project(self):
        card_item = CardItem.objects.create(
            card=self.card,
            project=self.project,
        )
        label = card_item.get_log_label()
        self.assertEqual(label, f"Item ({self.project.title})")

    def test_card_item_get_log_label_comment_short(self):
        card_item = CardItem.objects.create(
            card=self.card, comment="Short comment"  # less than 50 char
        )
        label = card_item.get_log_label()
        self.assertEqual(label, "Item (Short comment)")

    def test_card_item_get_log_label_comment_long(self):
        hundred_x = "x" * 100

        card_item = CardItem.objects.create(
            card=self.card,
            comment=hundred_x,
        )
        label = card_item.get_log_label()
        fifty_x_and_ellipsis = "x" * 50 + "..."
        self.assertEqual(label, f"Item ({fifty_x_and_ellipsis})")

    def test_board_log_list(self):
        self.client.force_login(user=self.user)
        self.client.put(  # Create log
            reverse("board_detail", kwargs={"pk": self.board.id}),
            {"name": "Board 1 Name Updated", "owner": self.user.id},
        )

        response = self.client.get(
            reverse("board_log_list", kwargs={"pk": self.board.id})
        )
        messages = [x["message"] for x in response.json()["results"]]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(
            f"Board {self.board.name} Name Updated updated by {self.user}",
            messages,
        )
