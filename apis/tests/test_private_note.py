from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from core.models import (
    Project,
    User,
    ProjectAccess,
    Comment,
    Task,
    PrivateNote,
)


class PrivateNoteTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username="user1")
        cls.user_2 = User.objects.create(username="user2")
        cls.user_3 = User.objects.create(username="user3")

        cls.project = Project.objects.create(
            title="Testing Project 1 XXX",
            owner=cls.user,
            description="Description of project 1",
        )
        cls.project_2 = Project.objects.create(
            title="Testing Project 2",
            owner=cls.user_2,
            description="Description of project 2",
        )

        ProjectAccess.objects.create(project=cls.project, user=cls.user_2)
        ProjectAccess.objects.create(project=cls.project, user=cls.user_3)

        cls.task_1_project_1_user_1 = Task.objects.create(
            project=cls.project, owner=cls.user, title="Task 1"
        )

        cls.note_1_task_1_user2 = PrivateNote.objects.create(
            task=cls.task_1_project_1_user_1,
            user=cls.user_2,
            note="Note 1 task 1 user 2",
        )

        cls.task_2_project_2_user_1 = Task.objects.create(
            project=cls.project_2, owner=cls.user, title="Task 2"
        )

        cls.note_2_task_2_user_2 = PrivateNote.objects.create(
            task=cls.task_2_project_2_user_1,
            user=cls.user_2,
            note="Note 2 task 2 user 2",
        )

        # Task owner note
        cls.note_3_task_1_user_1 = PrivateNote.objects.create(
            task=cls.task_1_project_1_user_1,
            user=cls.user,
            note="Note 3 task 1 user 1",
        )

    def test_private_note_list_not_authenticated(self):
        response = self.client.get(reverse("private_note_list"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_private_note_list_authenticated(self):
        self.client.force_login(self.user_2)
        response = self.client.get(reverse("private_note_list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result_ids = [x.get("id") for x in response.json().get("results")]
        self.assertIn(
            str(self.note_1_task_1_user2.id),
            result_ids,
        )

        self.assertNotIn(self.note_3_task_1_user_1.id.__str__(), result_ids)

    def test_private_note_list_no_notes(self):
        self.client.force_login(self.user_3)
        response = self.client.get(
            reverse("private_note_list")
            + f"?task={self.task_1_project_1_user_1.id}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get("results"), [])

    def test_private_note_task_filter(self):
        self.client.force_login(self.user_2)
        response = self.client.get(
            reverse("private_note_list")
            + f"?task={self.task_1_project_1_user_1.id}"
        )
        result_ids = [x.get("id") for x in response.json().get("results")]
        self.assertIn(str(self.note_1_task_1_user2.id), result_ids)
        self.assertNotIn(str(self.note_3_task_1_user_1.id), result_ids)

    def test_create_private_note_not_authenticated(self):
        response = self.client.post(
            reverse("private_note_list"),
            {
                "task_id": f"{self.note_1_task_1_user2.id}",
                "note": "this is note test",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_private_note(self):
        self.client.force_login(self.user_2)
        response = self.client.post(
            reverse("private_note_list"),
            {
                "task": f"{self.task_1_project_1_user_1.id}",
                "note": "this is note test",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_private_note_no_note(self):
        self.client.force_login(self.user_2)
        response = self.client.post(
            reverse("private_note_list"),
            {
                "task": f"{self.task_1_project_1_user_1.id}",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_edit_own_pirvate_note(self):
        self.client.force_login(self.user_2)
        updated_note = "this is edited note"
        response = self.client.put(
            reverse(
                "private_note_detail",
                kwargs={"pk": self.note_1_task_1_user2.id},
            ),
            {"note": updated_note},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        private_note = PrivateNote.objects.get(id=self.note_1_task_1_user2.id)
        self.assertEqual(updated_note, private_note.note)

    def test_edit_own_pirvate_note_no_note(self):
        self.client.force_login(self.user_2)
        response = self.client.put(
            reverse(
                "private_note_detail",
                kwargs={"pk": self.note_1_task_1_user2.id},
            ),
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_edit_sombodies_else_note(self):
        self.client.force_login(self.user)
        updated_note = "this is edited note"
        response = self.client.put(
            reverse(
                "private_note_detail",
                kwargs={"pk": self.note_1_task_1_user2.id},
            ),
            {"note": updated_note},
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_private_note(self):
        self.client.force_login(self.user_2)
        response = self.client.delete(
            reverse(
                "private_note_detail",
                kwargs={"pk": self.note_1_task_1_user2.id},
            )
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_sombodies_else_private_note(self):
        self.client.force_login(self.user)
        response = self.client.delete(
            reverse(
                "private_note_detail",
                kwargs={"pk": self.note_1_task_1_user2.id},
            )
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
