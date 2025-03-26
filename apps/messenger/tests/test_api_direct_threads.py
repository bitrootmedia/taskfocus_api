import pytest
from django.urls import reverse
from rest_framework import status

from apps.messenger.models import DirectMessage, DirectMessageAck, DirectThread
from core.models import User


@pytest.mark.django_db
def test_list_direct_threads_no_messages(auth_client, direct_thread):
    response = auth_client.get(reverse("direct-thread-list"))
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["unseen_messages_count"] == 0


@pytest.mark.django_db
def test_list_direct_threads_with_unseen_message(auth_client, direct_thread, direct_message):
    response = auth_client.get(reverse("direct-thread-list"))
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["unseen_messages_count"] == 1


@pytest.mark.django_db
def test_list_direct_threads_with_seen_message(auth_client, direct_thread, direct_message, direct_message_ack):
    response = auth_client.get(reverse("direct-thread-list"))
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["unseen_messages_count"] == 0
