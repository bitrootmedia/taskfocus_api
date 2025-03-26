from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status

from apps.messenger.models import MessageAck


@pytest.mark.django_db
def test_user_can_access_messages(auth_client, thread, message):
    url = reverse("messages-list", kwargs={"thread_id": str(thread.id)})
    response = auth_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 1


@pytest.mark.django_db
def test_user_cannot_access_messages_without_permission(auth_client, thread, message, project):
    project.permissions.all().delete()
    url = reverse("messages-list", kwargs={"thread_id": str(thread.id)})
    response = auth_client.get(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
@patch("apps.messenger.api.WebsocketHelper")
def test_user_can_create_message(mock_websocket_helper, auth_client, thread, user):
    mock_ws_instance = mock_websocket_helper.return_value
    url = reverse("messages-list", kwargs={"thread_id": str(thread.id)})
    data = {"thread": thread.id, "content": "New message"}
    response = auth_client.post(url, data)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["content"] == "New message"
    mock_ws_instance.send.assert_called_once_with(
        f"thread_{thread.id}", "message_added", data={"content": "New message", "sender": f"{user.id}"}
    )


@pytest.mark.django_db
def test_user_cannot_create_message_without_permission(auth_client, thread, project):
    project.permissions.all().delete()
    url = reverse("messages-list", kwargs={"thread_id": str(thread.id)})
    data = {"thread": thread.id, "content": "New message"}
    response = auth_client.post(url, data)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_ack_messages_success(client, create_thread_with_messages):
    user1, _, thread, messages = create_thread_with_messages()
    client.force_authenticate(user1)
    url = reverse("messages-ack", kwargs={"thread_id": str(thread.id)})

    message_ids = [msg.id for msg in messages[:2]]
    response = client.post(url, data={"message_ids": message_ids})

    assert response.status_code == 200
    assert MessageAck.objects.filter(user=user1, message_id__in=message_ids).count() == 2


@pytest.mark.django_db
def test_ack_messages_idempotency(client, create_thread_with_messages):
    user1, _, thread, messages = create_thread_with_messages()
    client.force_authenticate(user1)
    url = reverse("messages-ack", kwargs={"thread_id": thread.id})

    message_id = messages[0].id

    # First acknowledgment
    response1 = client.post(url, {"message_ids": [message_id]})
    assert response1.status_code == 200
    assert MessageAck.objects.filter(user=user1, message_id=message_id).exists()

    # Second acknowledgment should not duplicate entries
    response2 = client.post(url, {"message_ids": [message_id]})
    assert response2.status_code == 200
    assert MessageAck.objects.filter(user=user1, message_id=message_id).count() == 1


@pytest.mark.django_db
def test_ack_messages_empty_list(client, create_thread_with_messages):
    user1, _, thread, _ = create_thread_with_messages()
    client.force_authenticate(user1)
    url = reverse("messages-ack", kwargs={"thread_id": str(thread.id)})

    response = client.post(url, data={"message_ids": []})
    assert response.status_code == 400
    assert response.json() == {"message_ids": ["This field is required."]}


@pytest.mark.django_db
def test_ack_messages_unauthorized(client, create_thread_with_messages):
    _, _, thread, messages = create_thread_with_messages()
    url = reverse("messages-ack", kwargs={"thread_id": str(thread.id)})

    message_ids = [msg.id for msg in messages[:2]]
    response = client.post(url, data={"message_ids": message_ids})

    assert response.status_code == 403
