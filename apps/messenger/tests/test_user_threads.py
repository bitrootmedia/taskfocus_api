import pytest
from django.urls import reverse
from rest_framework import status
from freezegun import freeze_time


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
    auth_client = make_auth_client(user=user)

    project = make_project(owner=user, members=[thread_user1, thread_user2])
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
    ]
    assert response_data == expected_data


@pytest.mark.django_db
@freeze_time("2023-01-01T12:00:00Z")
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
    ]
    assert response_data == expected_data
