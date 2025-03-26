from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.test import APITestCase

from core.models import User


class UsersTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username="user1", email="user@some.domain")
        cls.user_2 = User.objects.create(username="user2")

    def test_api_sends_reset_password_email(self):
        r = self.client.post(
            reverse("rest_password_reset"),
            {"email": self.user.email},
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.json()["detail"], "Password reset e-mail has been sent.")

        encoded_user_uid = urlsafe_base64_encode(force_bytes(self.user.pk))

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Password Reset")
        self.assertIn(settings.WEB_APP_URL, mail.outbox[0].body)
        self.assertIn(encoded_user_uid, mail.outbox[0].body)

    def test_api_change_password(self):
        token = default_token_generator.make_token(self.user)
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))

        r = self.client.post(
            reverse("rest_password_reset_confirm"),
            {
                "uid": uid,
                "token": token,
                "new_password1": "n3wP4ssw0rd420",
                "new_password2": "n3wP4ssw0rd420",
            },
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(
            r.json()["detail"],
            "Password has been reset with the new password.",
        )

    def test_api_change_password_bad_uid(self):
        r = self.client.post(
            reverse("rest_password_reset_confirm"),
            {
                "uid": "baduid",
                "token": "badtoken",
                "new_password1": "123456",
                "new_password2": "abcdef",
            },
        )

        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("uid", r.json())

    def test_api_change_password_bad_passwords(self):
        token = default_token_generator.make_token(self.user)
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        r = self.client.post(
            reverse("rest_password_reset_confirm"),
            {
                "uid": uid,
                "token": token,
                "new_password1": "",
                "new_password2": "",
            },
        )

        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("new_password1", r.json())
        self.assertIn("new_password2", r.json())
