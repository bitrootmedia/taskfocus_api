from time import sleep

import pytest
from django.urls import reverse
from freezegun import freeze_time
from rest_framework import status


@pytest.mark.django_db
@freeze_time("2023-01-01T12:00:00Z")
def test_user_threads_no_acks(
    make_auth_client,
    make_user,
    make_thread,
    make_message,
    make_project,
    make_direct_thread,
    make_direct_message,
):
    user = make_user()
    thread_user1 = make_user()
    thread_user2 = make_user()
    thread_user3 = make_user()
    auth_client = make_auth_client(user=user)

    project = make_project(owner=user, members=[thread_user1, thread_user2, thread_user3])
    thread = make_thread(project=project)
    make_thread()
    make_message(thread=thread, sender=user)
    make_message(thread=thread, sender=thread_user1)
    make_message(thread=thread, sender=thread_user2)
    make_message(thread=thread, sender=thread_user1)
    make_message(thread=thread, sender=thread_user1)

    url = reverse("users")
    response = auth_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    expected_data = [
        {
            "user": {"id": str(thread_user1.id), "username": f"{thread_user1.username}", "image": None},
            "unread_count": 3,
            "last_unread_message_date": "2023-01-01T12:00:00Z",
        },
        {
            "user": {"id": str(thread_user2.id), "username": str(thread_user2.username), "image": None},
            "unread_count": 1,
            "last_unread_message_date": "2023-01-01T12:00:00Z",
        },
        {
            "user": {"id": str(thread_user3.id), "username": str(thread_user3.username), "image": None},
            "unread_count": 0,
            "last_unread_message_date": None,
        },
    ]
    assert response_data == expected_data


@pytest.mark.django_db
def test_user_threads_some_acks(
    make_auth_client,
    make_user,
    make_thread,
    make_message,
    make_project,
    make_direct_thread,
    make_direct_message,
    make_direct_thread_ack,
    make_thread_ack,
):
    user = make_user()
    thread_user1 = make_user()
    thread_user2 = make_user()
    auth_client = make_auth_client(user=user)

    project = make_project(owner=user, members=[thread_user1, thread_user2])
    thread = make_thread(project=project)
    make_thread()
    make_message(thread=thread, sender=user)
    make_message(thread=thread, sender=thread_user1)
    make_message(thread=thread, sender=thread_user2)
    make_thread_ack(thread=thread, user=user)
    make_message(thread=thread, sender=thread_user1)
    message = make_message(thread=thread, sender=thread_user1)

    url = reverse("users")
    response = auth_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    expected_data = [
        {
            "user": {"id": str(thread_user1.id), "username": f"{thread_user1.username}", "image": None},
            "unread_count": 2,
            "last_unread_message_date": message.created_at.isoformat().replace("+00:00", "Z"),
        },
        {
            "user": {"id": str(thread_user2.id), "username": str(thread_user2.username), "image": None},
            "unread_count": 0,
            "last_unread_message_date": None,
        },
    ]
    assert response_data == expected_data


@pytest.mark.django_db
@freeze_time("2023-01-01T12:00:00Z")
def test_user_threads_with_query_filter(
    make_auth_client,
    make_user,
    make_thread,
    make_message,
    make_project,
):
    user = make_user()
    thread_user1 = make_user(username="alice_smith")
    thread_user2 = make_user(username="bob_jones")
    thread_user3 = make_user(username="alice_brown")
    auth_client = make_auth_client(user=user)

    project = make_project(owner=user, members=[thread_user1, thread_user2, thread_user3])
    thread = make_thread(project=project)
    make_message(thread=thread, sender=user)
    make_message(thread=thread, sender=thread_user1)
    make_message(thread=thread, sender=thread_user2)
    make_message(thread=thread, sender=thread_user3)

    # Test filtering by username 'alice'
    url = reverse("users")
    response = auth_client.get(f"{url}?query=alice")

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert len(response_data) == 2

    # Verify only users with 'alice' in username are returned
    usernames = [user_data["user"]["username"] for user_data in response_data]
    assert "alice_smith" in usernames
    assert "alice_brown" in usernames
    assert "bob_jones" not in usernames

    # Test filtering by username 'bob'
    response = auth_client.get(f"{url}?query=bob")

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert len(response_data) == 1
    assert response_data[0]["user"]["username"] == "bob_jones"
