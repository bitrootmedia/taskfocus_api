from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from core.models import User, Notification, NotificationAck


class NotificationTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_1 = User.objects.create(username="user1")

    def test_notification_not_authenticated(self):
        response = self.client.get(reverse("project_access_list"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # def test_api_project_access_list_authenticated(self):
    #     self.client.force_login(self.user_1)
    #     response = self.client.get(reverse("project_access_list"))
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #
        # results = response.json().get("results")
        #
        # found = False
        # for res in results:
        #     if res.get("project") == self.project_1_user_1.id.__str__():
        #         if res.get("user").get("id") == self.user_2.id.__str__():
        #             found = True
        #
        # self.assertTrue(found)
#