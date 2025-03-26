import uuid

import pytest
from django.urls import reverse
from rest_framework import status

from apps.messenger.models import Thread
from core.models import User


@pytest.mark.django_db
def test_user_threads(auth_client, thread):
    response = auth_client.get(reverse("thread-list"))
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) > 0


@pytest.mark.django_db
def test_cannot_see_other_threads(auth_client, thread):
    other_thread = Thread.objects.create(
        task_id=uuid.uuid4(),
        user=User.objects.create_user(username="other", password="password"),
    )
    response = auth_client.get(reverse("thread-list"))
    assert response.status_code == status.HTTP_200_OK
    assert response.data["results"]
    assert other_thread.id not in [t["id"] for t in response.data["results"]]


@pytest.mark.django_db
def test_unread_count_api(auth_client, user, thread, message):
    url = reverse("thread-list")
    response = auth_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["results"][0]["unread_count"] == 1


@pytest.mark.django_db
def test_unread_count_api_when_message_was_ack(auth_client, user, thread, message, message_ack):
    url = reverse("thread-list")
    response = auth_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["results"][0]["unread_count"] == 0
