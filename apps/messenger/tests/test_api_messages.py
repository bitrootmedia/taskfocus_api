from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
def test_user_can_access_messages(make_user, make_auth_client, make_thread, make_project, make_message):
    user = make_user()
    project = make_project(owner=user)
    auth_client = make_auth_client(user=user)
    thread = make_thread(user=user, project=project)
    make_message(sender=user, thread=thread)
    url = reverse("messages-list", kwargs={"thread_id": str(thread.id)})
    response = auth_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 1


@pytest.mark.django_db
def test_user_cannot_access_messages_without_permission(make_user, make_auth_client, make_thread, make_project):
    user = make_user()
    project = make_project()
    auth_client = make_auth_client(user=user)
    thread = make_thread(user=user, project=project)
    project.permissions.all().delete()
    url = reverse("messages-list", kwargs={"thread_id": str(thread.id)})
    response = auth_client.get(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
@patch("apps.messenger.api.WebsocketHelper")
def test_user_can_create_message(mock_websocket_helper, make_user, make_auth_client, make_thread, make_project):
    mock_ws_instance = mock_websocket_helper.return_value
    user = make_user()
    project = make_project(owner=user)
    auth_client = make_auth_client(user=user)
    thread = make_thread(user=user, project=project)
    url = reverse("messages-list", kwargs={"thread_id": str(thread.id)})
    data = {"thread": thread.id, "content": "New message"}
    response = auth_client.post(url, data)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["content"] == "New message"
    mock_ws_instance.send.assert_called_once_with(
        f"thread_{thread.id}", "message_added", data={"content": "New message", "sender": f"{user.id}"}
    )


@pytest.mark.django_db
def test_user_cannot_create_message_without_permission(make_user, make_auth_client, make_thread, make_project):
    project = make_project()
    user = make_user()
    auth_client = make_auth_client(user=user)
    thread = make_thread(user=user, project=project)
    project.permissions.all().delete()
    url = reverse("messages-list", kwargs={"thread_id": str(thread.id)})
    data = {"thread": thread.id, "content": "New message"}
    response = auth_client.post(url, data)
    assert response.status_code == status.HTTP_403_FORBIDDEN
