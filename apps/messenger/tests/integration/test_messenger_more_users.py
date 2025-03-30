from datetime import datetime

import pytest
from rest_framework import status

from core.models import ProjectAccess


@pytest.mark.django_db
def test_messenger_with_four_users_complex(make_auth_client, make_user, make_project):
    """
    1. user1 creates thread
    2. user1 sends a message
    3. user2, user3, and user4 list threads and see the unseen message
    4. user2 acks the message but does not send a new one
    5. user3 acks the message and sends a new one
    6. user4 lists threads and sees 1 unseen message
    7. user4 acks the message but also sends a new message
    8. user2, user3, and user4 list threads and see no unseen messages
    9. user1 lists threads and sees all new messages
    10. user1 sends a new message and checks unread counts
    11. user4 lists threads and sees the latest unread message
    """

    integration_user1 = make_user()
    integration_user2 = make_user()
    integration_user3 = make_user()
    integration_user4 = make_user()
    user1_auth_client = make_auth_client(user=integration_user1)
    user2_auth_client = make_auth_client(user=integration_user2)
    user3_auth_client = make_auth_client(user=integration_user3)
    user4_auth_client = make_auth_client(user=integration_user4)

    project = make_project(owner=integration_user1, members=[integration_user2, integration_user3, integration_user4])

    # User1 creates thread
    response = user1_auth_client.post("/messenger/threads/", {"project": str(project.id)})
    assert response.status_code == status.HTTP_201_CREATED
    created_thread = response.json()
    assert created_thread["project"] == str(project.id)
    assert created_thread["unread_count"] == 0
    assert created_thread["task"] is None

    # User1 sends a message
    thread_id = created_thread["id"]
    response = user1_auth_client.post(f"/messenger/threads/{thread_id}/messages/", {"content": "Hello, Users!"})
    assert response.status_code == status.HTTP_201_CREATED
    created_message = response.json()
    assert created_message["content"] == "Hello, Users!"
    assert created_message["thread"] == str(thread_id)
    assert created_message["sender"] == str(integration_user1.id)

    # User2 lists threads and sees 1 unseen message
    response = user2_auth_client.get("/messenger/threads/")
    assert response.status_code == status.HTTP_200_OK
    results = response.json()["results"]
    assert len(results) == 1
    thread = results[0]
    assert thread["id"] == str(thread_id)
    assert thread["project"] == str(project.id)
    assert thread["unread_count"] == 1

    # User2 acks the message but does not send any new messages
    response = user2_auth_client.post(
        f"/messenger/threads/{thread_id}/ack/",
        {"seen_at": datetime.now()},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK

    # User2 lists threads again and sees 0 unseen messages
    response = user2_auth_client.get("/messenger/threads/")
    assert response.status_code == status.HTTP_200_OK
    results = response.json()["results"]
    assert len(results) == 1
    thread = results[0]
    assert thread["id"] == str(thread_id)
    assert thread["project"] == str(project.id)
    assert thread["unread_count"] == 0

    # User3 lists threads and sees 1 unseen message
    response = user3_auth_client.get("/messenger/threads/")
    assert response.status_code == status.HTTP_200_OK
    results = response.json()["results"]
    assert len(results) == 1
    thread = results[0]
    assert thread["id"] == str(thread_id)
    assert thread["project"] == str(project.id)
    assert thread["unread_count"] == 1

    # User3 acks the message and sends a new one
    response = user3_auth_client.post(
        f"/messenger/threads/{thread_id}/ack/",
        {"seen_at": datetime.now()},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    response = user3_auth_client.post(f"/messenger/threads/{thread_id}/messages/", {"content": "Message from User3!"})
    assert response.status_code == status.HTTP_201_CREATED

    # User4 lists threads and sees 2 unseen message (User1's and User3's messages)
    response = user4_auth_client.get("/messenger/threads/")
    assert response.status_code == status.HTTP_200_OK
    results = response.json()["results"]
    assert len(results) == 1
    thread = results[0]
    assert thread["id"] == str(thread_id)
    assert thread["project"] == str(project.id)
    assert thread["unread_count"] == 2

    # User4 acks the messages
    response = user4_auth_client.post(
        f"/messenger/threads/{thread_id}/ack/",
        {"seen_at": datetime.now()},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK

    # User1 acks messages
    response = user1_auth_client.post(
        f"/messenger/threads/{thread_id}/ack/",
        {"seen_at": datetime.now()},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK

    # User2 acks messages
    response = user2_auth_client.post(
        f"/messenger/threads/{thread_id}/ack/",
        {"seen_at": datetime.now()},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK

    # User 4 sends new message
    response = user4_auth_client.post(f"/messenger/threads/{thread_id}/messages/", {"content": "Message from User4!"})
    assert response.status_code == status.HTTP_201_CREATED

    # User1, User2, User3 list threads and see User4's unseen message

    for auth_client in [user1_auth_client, user2_auth_client, user3_auth_client]:
        response = auth_client.get("/messenger/threads/")
        assert response.status_code == status.HTTP_200_OK
        results = response.json()["results"]
        assert len(results) == 1
        thread = results[0]
        assert thread["id"] == str(thread_id)
        assert thread["project"] == str(project.id)
        assert thread["unread_count"] == 1

    # User1 sends a new message
    response = user1_auth_client.post(
        f"/messenger/threads/{thread_id}/messages/", {"content": "New message from User1!"}
    )
    assert response.status_code == status.HTTP_201_CREATED

    # User4 lists threads and sees the latest unread message
    response = user4_auth_client.get("/messenger/threads/")
    assert response.status_code == status.HTTP_200_OK
    results = response.json()["results"]
    assert len(results) == 1
    thread = results[0]
    assert thread["id"] == str(thread_id)
    assert thread["project"] == str(project.id)
    assert thread["unread_count"] == 1

    # User4 acks User1's new message
    response = user4_auth_client.post(
        f"/messenger/threads/{thread_id}/ack/",
        {"seen_at": datetime.now()},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK

    # Final check - User4 lists threads again and sees no unread messages
    response = user4_auth_client.get("/messenger/threads/")
    assert response.status_code == status.HTTP_200_OK
    results = response.json()["results"]
    assert len(results) == 1
    thread = results[0]
    assert thread["id"] == str(thread_id)
    assert thread["project"] == str(project.id)
    assert thread["unread_count"] == 0
