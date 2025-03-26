import pytest
from django.urls import reverse
from rest_framework import status

from apps.messenger.models import DirectMessage, DirectMessageAck, DirectThread
from core.models import User


@pytest.mark.django_db
def test_list_direct_threads(auth_client, direct_thread):
    response = auth_client.get(reverse("direct-thread-list"))
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) > 0


@pytest.mark.django_db
def test_list_direct_threads_with_unseen_count(auth_client, direct_thread, direct_message):
    response = auth_client.get(reverse("direct-thread-list-with-unseen-count"))
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) > 0
    assert "unseen_messages_count" in response.data[0]


@pytest.mark.django_db
def test_unseen_messages_count(auth_client, user, direct_thread, direct_message):
    DirectMessageAck.objects.create(message=direct_message, user=user)
    response = auth_client.get(reverse("direct-thread-list-with-unseen-count"))
    assert response.status_code == status.HTTP_200_OK
    assert response.data[0]["unseen_messages_count"] == 0


@pytest.mark.django_db
def test_cannot_see_other_users_threads(no_thread_user_auth_client, no_thread_user, direct_thread):
    response = no_thread_user_auth_client.get(reverse("direct-thread-list"))
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 0
