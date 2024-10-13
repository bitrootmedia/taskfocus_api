from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from core.models import User, Note


class TestNotes(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username="user1")
        cls.user_2 = User.objects.create(username="user2")
        cls.user_3 = User.objects.create(username="user3")

        cls.note = Note.objects.create(
            user=cls.user,
            title="Test Note",
            content="Test Note\nContent here",
        )
        cls.note_2 = Note.objects.create(
            user=cls.user_2,
            title="Test Note 2",
            content="Test Note 2\nContent 2 here",
        )
        cls.note_3 = Note.objects.create(
            user=cls.user,
            title="Test Note 3",
            content="Test Note 3\nContent 3 here",
        )

    def test_note_list_not_authenticated(self):
        response = self.client.get(reverse("note_list"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_note_list_authenticated(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("note_list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        note_ids = [x.get("id") for x in response.json().get("results")]
        self.assertListEqual(
            note_ids,
            [
                str(self.note_3.id),  # Order by -updated_at so latest first
                str(self.note.id),
            ],
        )

    def test_note_list_no_notes(self):
        self.client.force_authenticate(user=self.user_3)
        response = self.client.get(reverse("note_list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get("results"), [])

    def test_create_note_with_title(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse("note_list"),
            {"content": "First line is the title\nContent here"},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            "First line is the title", response.json().get("title")
        )

    def test_create_note_first_newlines(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse("note_list"),
            {"content": "\n\n\nContent here"},  # first line empty
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual("Content here", response.json().get("title"))

    def test_get_other_users_note(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            reverse("note_detail", kwargs={"pk": self.note_2.id}),
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_edit_own_note(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.put(
            reverse("note_detail", kwargs={"pk": self.note.id}),
            {"content": "Updated Title\nUpdated Content here"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, "Updated Title")
        self.assertEqual(
            self.note.content, "Updated Title\nUpdated Content here"
        )

    def test_edit_other_users_note(self):
        self.client.force_authenticate(user=self.user_2)
        response = self.client.put(
            reverse("note_detail", kwargs={"pk": self.note.id}),
            {
                "content": "Updated Content",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_note(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(
            reverse("note_detail", kwargs={"pk": self.note.id}),
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_other_users_note(self):
        self.client.force_authenticate(user=self.user_3)
        response = self.client.delete(
            reverse("note_detail", kwargs={"pk": self.note.id}),
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
