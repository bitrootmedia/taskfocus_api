import uuid

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from apps.messenger.models import Thread, ThreadAck
from core.models import User


@pytest.mark.django_db
def test_create_thread(auth_client, user, project):
    payload = {"project_id": str(project.id)}
    response = auth_client.post(reverse("thread-list"), payload)

    assert response.status_code == status.HTTP_201_CREATED
    thread = Thread.objects.get(id=response.data["id"])
    assert thread.project_id == project.id
    assert thread.user.id == user.id


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
def test_unread_count_api(auth_client, user, other_user, thread, message):
    url = reverse("thread-list")
    response = auth_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["results"][0]["unread_count"] == 0

    auth_client.force_authenticate(other_user)
    response = auth_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["results"][0]["unread_count"] == 1


@pytest.mark.django_db
def test_unread_count_api_when_message_was_ack(auth_client, user, thread, message, thread_ack):
    url = reverse("thread-list")
    response = auth_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["results"][0]["unread_count"] == 0


@pytest.mark.django_db
def test_ack_direct_thread(auth_client, thread, user):
    assert ThreadAck.objects.count() == 0
    url = reverse("thread-ack", args=[thread.id])
    seen_at = timezone.now()
    response = auth_client.post(url, {"seen_at": seen_at}, format="json")
    assert response.status_code == status.HTTP_200_OK
    assert ThreadAck.objects.count() == 1
    thread_ack = ThreadAck.objects.first()
    assert thread_ack.user == user
    assert thread_ack.seen_at == seen_at
