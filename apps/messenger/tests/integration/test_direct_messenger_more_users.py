from datetime import datetime, timedelta

import pytest
from rest_framework import status


@pytest.mark.django_db
def test_direct_messenger_three_users(auth_client, integration_user1, integration_user2, integration_user3):
    """
    Integration test for direct messaging between three users.
    """

    # User1 creates a thread with User2 and User3
    auth_client.force_authenticate(integration_user1)
    response = auth_client.post(
        "/messenger/direct-threads/",
        {"users": [str(integration_user2.id), str(integration_user3.id)]},
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED
    created_thread = response.json()
    thread_id = created_thread["id"]

    # User1 sends a message
    response = auth_client.post(
        f"/messenger/direct-threads/{thread_id}/messages/",
        {"content": "Hello, everyone!"},
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED

    # User2 lists threads and sees 1 unseen message
    auth_client.force_authenticate(integration_user2)
    response = auth_client.get("/messenger/direct-threads/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["results"][0]["unread_count"] == 1

    # User3 lists threads and sees 1 unseen message
    auth_client.force_authenticate(integration_user3)
    response = auth_client.get("/messenger/direct-threads/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["results"][0]["unread_count"] == 1

    # User2 acks the message
    auth_client.force_authenticate(integration_user2)
    response = auth_client.post(
        f"/messenger/direct-threads/{thread_id}/ack/",
        {"seen_at": datetime.now()},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK

    # User2 lists threads and sees 0 unseen message
    response = auth_client.get("/messenger/direct-threads/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["results"][0]["unread_count"] == 0

    # User3 should still see 1 unseen message
    auth_client.force_authenticate(integration_user3)
    response = auth_client.get("/messenger/direct-threads/")
    assert response.json()["results"][0]["unread_count"] == 1

    # User1 sends another message
    auth_client.force_authenticate(integration_user1)
    response = auth_client.post(
        f"/messenger/direct-threads/{thread_id}/messages/",
        {"content": "Message 3"},
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED

    # User3 sees 2 unseen messages
    auth_client.force_authenticate(integration_user3)
    response = auth_client.get("/messenger/direct-threads/")
    assert response.json()["results"][0]["unread_count"] == 2

    # User3 acks all messages
    response = auth_client.post(
        f"/messenger/direct-threads/{thread_id}/ack/",
        {"seen_at": datetime.now()},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK

    # User2 acks all messages
    auth_client.force_authenticate(integration_user2)
    response = auth_client.post(
        f"/messenger/direct-threads/{thread_id}/ack/",
        {"seen_at": datetime.now()},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK

    # User1 sends two more messages
    auth_client.force_authenticate(integration_user1)
    response = auth_client.post(
        f"/messenger/direct-threads/{thread_id}/messages/",
        {"content": "Message 1."},
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED

    response = auth_client.post(
        f"/messenger/direct-threads/{thread_id}/messages/",
        {"content": "Message 2."},
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED

    # Both User2 and User3 should see 2 unseen messages
    auth_client.force_authenticate(integration_user2)
    response = auth_client.get("/messenger/direct-threads/")
    assert response.json()["results"][0]["unread_count"] == 2

    auth_client.force_authenticate(integration_user3)
    response = auth_client.get("/messenger/direct-threads/")
    assert response.json()["results"][0]["unread_count"] == 2

    # User3 acks all messages
    auth_client.force_authenticate(integration_user3)
    response = auth_client.post(
        f"/messenger/direct-threads/{thread_id}/ack/",
        {"seen_at": datetime.now()},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK

    # User2 changes thread ack (potential mark as unread feature)
    auth_client.force_authenticate(integration_user2)
    yesterday = datetime.now() - timedelta(days=1)
    response = auth_client.post(
        f"/messenger/direct-threads/{thread_id}/ack/",
        {"seen_at": yesterday},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK

    # User2 should all 4 messages as unread
    auth_client.force_authenticate(integration_user2)
    response = auth_client.get("/messenger/direct-threads/")
    assert response.json()["results"][0]["unread_count"] == 4
