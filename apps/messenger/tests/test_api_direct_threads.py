from datetime import datetime

import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
def test_list_direct_threads_no_messages(auth_client, direct_thread):
    response = auth_client.get(reverse("direct-thread-list"))
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["unread_count"] == 0


@pytest.mark.django_db
def test_list_direct_threads_with_unseen_message(auth_client, other_user, direct_thread, direct_message):
    response = auth_client.get(reverse("direct-thread-list"))
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["unread_count"] == 0

    auth_client.force_authenticate(other_user)
    response = auth_client.get(reverse("direct-thread-list"))
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["unread_count"] == 1


@pytest.mark.django_db
def test_list_direct_threads_with_seen_message(auth_client, user, other_user, direct_thread, direct_message):
    response = auth_client.get(reverse("direct-thread-list"))
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["unread_count"] == 0

    auth_client.force_authenticate(other_user)
    response = auth_client.get(reverse("direct-thread-list"))
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["unread_count"] == 1


@pytest.mark.django_db
def test_ack_direct_messages_success(auth_client, direct_thread, direct_message):
    user = direct_thread.users.first()
    auth_client.force_authenticate(user)
    url = reverse("direct-thread-ack", kwargs={"pk": str(direct_thread.id)})
    response = auth_client.post(url, {"seen_at": datetime.now()})

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_ack_direct_messages_empty_list(auth_client, direct_thread):
    user = direct_thread.users.first()
    auth_client.force_authenticate(user)
    url = reverse("direct-thread-ack", kwargs={"pk": str(direct_thread.id)})

    response = auth_client.post(url, {"message_ids": []})
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_ack_direct_messages_unauthorized(client, direct_thread, direct_message):
    url = reverse("direct-thread-ack", kwargs={"pk": str(direct_thread.id)})
    response = client.post(url, {"message_ids": [str(direct_message.id)]})
    assert response.status_code == status.HTTP_403_FORBIDDEN
