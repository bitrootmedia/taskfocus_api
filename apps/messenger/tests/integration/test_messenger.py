from datetime import datetime

import pytest
from rest_framework import status

from core.models import ProjectAccess


@pytest.mark.django_db
def test_messenger(make_auth_client, make_user, make_project, make_thread):
    """
    1. user1 creates thread - its not supported yet so thread was created by fixture
    2. user1 creates message
    3. user2 list threads and sees unseen message
    4. user2 acks message
    5. user2 list threads - no unseen messages
    6. user2 creates 2 messages
    7. user1 list threads and sees 2 unseen messages
    """
    integration_user1 = make_user()
    integration_user2 = make_user()
    user1_auth_client = make_auth_client(user=integration_user1)
    user2_auth_client = make_auth_client(user=integration_user2)

    project = make_project(owner=integration_user1, members=[integration_user2])
    thread = make_thread(project=project)

    # User1 sends message
    thread_id = thread.id
    response = user1_auth_client.post(f"/messenger/conversations/{thread_id}", {"content": "Hello, User2!"})
    assert response.status_code == status.HTTP_201_CREATED
    created_message = response.json()
    assert created_message["content"] == "Hello, User2!"
    assert created_message["thread"] == str(thread_id)
    assert created_message["sender"] == str(integration_user1.id)

    # User2 opens chat and sees all unread users
    response = user2_auth_client.get("/messenger/users")
    assert response.status_code == status.HTTP_200_OK
    results = response.json()
    assert len(results) == 1
    assert results[0]["user"]["id"] == str(integration_user1.id)
    assert results[0]["unread_count"] == 1
    assert results[0]["last_unread_message_date"] is not None

    # User2 lists all unread threads
    response = user2_auth_client.get("/messenger/unread-threads")
    assert response.status_code == status.HTTP_200_OK
    results = response.json()
    assert len(results) == 1
    data = results[0]
    assert data["project"]["id"] == str(project.id)
    assert data["thread"] == str(thread.id)
    assert data["unread_count"] == 1

    # User2 can click on User1 and see all threads
    response = user2_auth_client.get(f"/messenger/threads/{integration_user1.id}")
    assert response.status_code == status.HTTP_200_OK
    results = response.json()
    assert len(results) == 1
    data = results[0]
    assert data["project"]["id"] == str(project.id)
    assert data["type"] == "project"
    assert data["thread"] == str(thread_id)
    assert data["unread_count"] == 1

    # User2 can click on specific thread and list messages
    response = user2_auth_client.get(f"/messenger/conversations/{thread.id}")
    assert response.status_code == status.HTTP_200_OK
    results = response.json()
    print(results)
    assert len(results) == 1
    data = results[0]
    assert data["sender"] == str(integration_user1.id)
    assert data["content"] == "Hello, User2!"
    assert data["thread"] == str(thread_id)

    # User2 can send a message to thread
    response = user2_auth_client.post(
        f"/messenger/conversations/{thread_id}",
        {"content": "Hey User1"},
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED

    # User2 list threads again and sees 0 unseen message
    response = user2_auth_client.get("/messenger/unread-threads")
    assert response.status_code == status.HTTP_200_OK
    results = response.json()
    assert len(results) == 0

    response = user2_auth_client.get("/messenger/users")
    assert response.status_code == status.HTTP_200_OK
    results = response.json()
    assert len(results) == 0
