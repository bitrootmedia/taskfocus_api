from datetime import datetime

import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
def test_list_direct_threads_no_messages(make_auth_client, make_user, make_direct_thread):
    user = make_user()
    auth_client = make_auth_client(user=user)
    make_direct_thread(users=[user])
    response = auth_client.get(reverse("direct-thread-list"))
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["unread_count"] == 0


@pytest.mark.django_db
def test_list_direct_threads_with_unseen_message(make_user, make_auth_client, make_direct_thread, make_direct_message):
    user = make_user()
    other_user = make_user()
    auth_client = make_auth_client(user=user)
    thread = make_direct_thread(users=[user, other_user])
    make_direct_message(thread=thread, sender=user)

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
def test_list_direct_threads_with_seen_message(make_auth_client, make_user, make_direct_thread, make_direct_message):
    user = make_user()
    other_user = make_user()
    auth_client = make_auth_client(user=user)

    direct_thread = make_direct_thread(users=[user, other_user])
    make_direct_message(thread=direct_thread, sender=user)
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
def test_ack_direc_messages_success(make_auth_client, make_direct_thread):
    direct_thread = make_direct_thread()
    user = direct_thread.users.first()
    auth_client = make_auth_client(user=user)
    url = reverse("direct-thread-ack", kwargs={"pk": str(direct_thread.id)})
    response = auth_client.post(url, {"seen_at": datetime.now()})

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_ack_direct_messages_empty_list(make_auth_client, make_direct_thread):
    direct_thread = make_direct_thread()
    user = direct_thread.users.first()
    auth_client = make_auth_client(user=user)
    url = reverse("direct-thread-ack", kwargs={"pk": str(direct_thread.id)})

    response = auth_client.post(url, {"message_ids": []})
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_ack_direct_messages_unauthorized(client, make_direct_thread, make_direct_message):
    direct_thread = make_direct_thread()
    direct_message = make_direct_message(thread=direct_thread)
    url = reverse("direct-thread-ack", kwargs={"pk": str(direct_thread.id)})
    response = client.post(url, {"message_ids": [str(direct_message.id)]})
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_create_thread_existing(make_user, make_auth_client, make_direct_thread):
    user = make_user()
    other_user = make_user()
    auth_client = make_auth_client(user=user)
    direct_thread = make_direct_thread(users=[user, other_user])
    data = {"users": [str(user.id), str(other_user.id)]}

    response = auth_client.post(reverse("direct-thread-list"), data, format="json")
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()

    assert "unread_count" in response_data
    assert response_data["unread_count"] >= 0
    assert response_data["id"] == str(direct_thread.id)


@pytest.mark.django_db
def test_retrieve_direct_thread(make_user, make_auth_client, make_direct_thread):
    user = make_user()
    auth_client = make_auth_client(user=user)
    direct_thread = make_direct_thread(users=[user])
    url = reverse("direct-thread-detail", args=[str(direct_thread.id)])
    response = auth_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == str(direct_thread.id)


@pytest.mark.django_db
def test_retrieve_direct_thread_not_found(make_auth_client):
    auth_client = make_auth_client()
    url = reverse("direct-thread-detail", args=[999])
    response = auth_client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND
