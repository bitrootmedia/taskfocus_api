from unittest.mock import patch

import pytest

from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
def test_user_can_access_messages(auth_client, thread, message):
    url = reverse("message-list", kwargs={"thread_id": thread.id})
    response = auth_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 1


@pytest.mark.django_db
def test_user_cannot_access_messages_without_permission(auth_client, thread, message, project):
    project.permissions.all().delete()
    url = reverse("message-list", kwargs={"thread_id": thread.id})
    response = auth_client.get(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_user_can_get_unread_count(auth_client, thread, message):
    url = reverse("message-unread-count", kwargs={"thread_id": thread.id})
    response = auth_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["unread_count"] == 1


@pytest.mark.django_db
def test_user_can_get_unread_count_when_message_was_acked(auth_client, thread, message, message_ack):
    url = reverse("message-unread-count", kwargs={"thread_id": thread.id})
    response = auth_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["unread_count"] == 0


@pytest.mark.django_db
def test_user_cannot_get_unread_count_without_permission(auth_client, thread, message, project):
    project.permissions.all().delete()
    url = reverse("message-unread-count", kwargs={"thread_id": thread.id})
    response = auth_client.get(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
@patch('messenger.api.WebsocketHelper')
def test_user_can_create_message(mock_websocket_helper, auth_client, thread, user):
    mock_ws_instance = mock_websocket_helper.return_value
    url = reverse("message-list", kwargs={"thread_id": thread.id})
    data = {"thread": thread.id, "content": "New message"}
    response = auth_client.post(url, data)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["content"] == "New message"
    mock_ws_instance.send.assert_called_once_with(
        f"thread_{thread.id}",
        "message_added",
        data={"content": "New message", "user": f"{user.id}"}
    )


@pytest.mark.django_db
def test_user_cannot_create_message_without_permission(auth_client, thread, project):
    project.permissions.all().delete()
    url = reverse("message-list", kwargs={"thread_id": thread.id})
    data = {"thread": thread.id, "content": "New message"}
    response = auth_client.post(url, data)
    assert response.status_code == status.HTTP_403_FORBIDDEN
