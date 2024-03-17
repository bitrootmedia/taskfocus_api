from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from core.models import User, UserReportsSchedule


class UserReportsScheduleTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username="user1", email="user@some.domain")
        cls.user_2 = User.objects.create(username="user2")

        cls.schedule = UserReportsSchedule.objects.get_or_create(user=cls.user)

        cls.view_url = reverse("user_reports_schedule")

    def test_reports_schedule_not_authenticated(self):
        response = self.client.get(self.view_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_reports_schedule_existing_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.view_url)
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("monthly_enabled", data)
        self.assertTrue(data["monthly_enabled"])

    def test_reports_schedule_gets_created_authenticated(self):
        self.client.force_login(self.user_2)
        response = self.client.get(self.view_url)
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("monthly_enabled", data)
        self.assertTrue(data["monthly_enabled"])

    def test_reports_schedule_update(self):
        self.client.force_login(self.user)

        response = self.client.put(self.view_url, {
            "daily_time": "15:30",
            "weekly_day": "2",
            "monthly_enabled": False
        })

        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data["daily_time"], "15:30")
        self.assertEqual(data["weekly_day"], 2)
        self.assertFalse(data["monthly_enabled"])

    def test_reports_schedule_update_missing_data(self):
        self.client.force_login(self.user)

        response = self.client.put(self.view_url, {
            "monthly_enabled": True,
            "monthly_day": "",
            "monthly_time": ""
        })

        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Please provide day and time for monthly reports", data['non_field_errors'])

    def test_reports_schedule_update_invalid_week_day(self):
        self.client.force_login(self.user)

        response = self.client.put(self.view_url, {
            "weekly_day": 8,
        })
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('"8" is not a valid choice.', data['weekly_day'])

    def test_reports_schedule_update_invalid_month_day(self):
        self.client.force_login(self.user)

        response = self.client.put(self.view_url, {
            "monthly_day": 40,
        })
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Ensure this value is less than or equal to 31.', data['monthly_day'])

    def test_reports_schedule_update_invalid_timezone(self):
        self.client.force_login(self.user)
        response = self.client.put(self.view_url, {
            "timezone": "Random/Timezone",
        })
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('"Random/Timezone" is not a valid choice.', data["timezone"])
