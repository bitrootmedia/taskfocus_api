from datetime import datetime

import pytest
from rest_framework import status


@pytest.mark.django_db
def test_direct_messenger(make_auth_client, make_user):
    """
    1. user1 creates direct thread
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

    # User1 creates thread
    response = user1_auth_client.post(
        "/messenger/direct-threads/", {"users": [str(integration_user2.id)]}, format="json"
    )
    assert response.status_code == status.HTTP_201_CREATED
    created_thread = response.json()
    assert len(created_thread["users"]) == 2
    assert str(integration_user1.id) in created_thread["users"]
    assert str(integration_user2.id) in created_thread["users"]

    # User1 sends message
    thread_id = created_thread["id"]
    response = user1_auth_client.post(f"/messenger/direct-threads/{thread_id}/messages/", {"content": "Hello, User2!"})
    assert response.status_code == status.HTTP_201_CREATED
    created_message = response.json()
    assert created_message["content"] == "Hello, User2!"
    assert created_message["thread"] == str(thread_id)
    assert created_message["sender"] == str(integration_user1.id)

    # User2 list threads and sees 1 unseen message
    response = user2_auth_client.get("/messenger/direct-threads/")
    assert response.status_code == status.HTTP_200_OK
    results = response.json()["results"]
    assert len(results) == 1
    thread = results[0]
    assert thread["id"] == str(thread_id)
    assert thread["unread_count"] == 1

    # User2 acks message
    response = user2_auth_client.post(
        f"/messenger/direct-threads/{thread_id}/ack/",
        {"seen_at": datetime.now()},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK

    # User2 list threads again and sees 0 unseen message
    response = user2_auth_client.get("/messenger/direct-threads/")
    assert response.status_code == status.HTTP_200_OK
    results = response.json()["results"]
    assert len(results) == 1
    thread = results[0]
    assert thread["id"] == str(thread_id)
    assert thread["unread_count"] == 0
