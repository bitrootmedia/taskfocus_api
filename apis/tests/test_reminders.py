from django.urls import reverse
from django.utils.timezone import now
from rest_framework import status
from rest_framework.test import APITestCase
from core.models import User, Reminder, Task


class RemindersTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_1 = User.objects.create(username="user1")
        cls.task_1 = Task.objects.create(owner=cls.user_1, title="Test")
        cls.task_2 = Task.objects.create(owner=cls.user_1, title="Test 2")
        cls.reminder_1 = Reminder.objects.create(
            created_by=cls.user_1,
            user=cls.user_1,
            task=cls.task_1,
            reminder_date=now(),
        )

    def test_reminders_not_authenticated(self):
        response = self.client.get(reverse("reminder_list"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_reminders_authenticated(self):
        self.client.force_login(self.user_1)
        response = self.client.get(reverse("reminder_list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.post(
            reverse("reminder_list"),
            data={
                "user": self.user_1.pk,
                "reminder_date": now(),
                "task": self.task_1.pk,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.client.post(
            reverse("reminder_list"),
            data={
                "user": self.user_1.pk,
                "reminder_date": now(),
                "task": self.task_1.pk,
                "message": "message 2",
            },
        )
        response = self.client.post(
            reverse("reminder_list"),
            data={
                "user": self.user_1.pk,
                "reminder_date": now(),
                "task": self.task_2.pk,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.get(reverse("reminder_list"))
        self.assertEqual(response.json().get("count"), 4)

        # test with filter
        response = self.client.get(
            reverse("reminder_list") + f"?task={self.task_2.pk}"
        )
        self.assertEqual(response.json().get("count"), 1)

        # close
        self.assertIsNone(self.reminder_1.closed_at)
        self.client.post(
            reverse("reminder_close", kwargs={"pk": self.reminder_1.pk})
        )
        reminder = Reminder.objects.get(pk=self.reminder_1.pk)
        self.assertIsNotNone(reminder.closed_at)
