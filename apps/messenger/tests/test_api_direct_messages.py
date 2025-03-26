import pytest
from django.urls import reverse
from rest_framework import status
from apps.messenger.models import DirectThread, DirectMessage, DirectMessageAck
from core.models import User


@pytest.mark.django_db
def test_user_can_access_direct_messages(auth_client, direct_thread, direct_message):
    url = reverse("directmessage-list", kwargs={"thread_id": direct_thread.id})
    response = auth_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 1


@pytest.mark.django_db
def test_user_cannot_access_direct_messages_without_permission(auth_client, direct_thread, direct_message):
    direct_thread.users.clear()
    url = reverse("directmessage-list", kwargs={"thread_id": direct_thread.id})
    response = auth_client.get(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_user_can_create_direct_message(auth_client, direct_thread, user):
    url = reverse("directmessage-list", kwargs={"thread_id": direct_thread.id})
    data = {"thread": direct_thread.id, "content": "New direct message"}
    response = auth_client.post(url, data)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["content"] == "New direct message"


@pytest.mark.django_db
def test_user_cannot_create_direct_message_without_permission(auth_client, direct_thread):
    direct_thread.users.clear()
    url = reverse("directmessage-list", kwargs={"thread_id": direct_thread.id})
    data = {"thread": direct_thread.id, "content": "New direct message"}
    response = auth_client.post(url, data)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_ack_direct_messages_success(auth_client, direct_thread, direct_messages):
    user = direct_thread.users.first()
    auth_client.force_authenticate(user)
    url = reverse("directmessage-ack-messages", kwargs={"thread_id": direct_thread.id})

    message_ids = [msg.id for msg in direct_messages[:2]]
    response = auth_client.post(url, data=[{"message": msg_id} for msg_id in message_ids])

    assert response.status_code == status.HTTP_200_OK
    assert DirectMessageAck.objects.filter(user=user, message_id__in=message_ids).count() == 2


@pytest.mark.django_db
def test_ack_direct_messages_idempotency(auth_client, direct_thread, direct_messages):
    user = direct_thread.users.first()
    auth_client.force_authenticate(user)
    url = reverse("directmessage-ack-messages", kwargs={"thread_id": direct_thread.id})

    message_id = direct_messages[0].id

    # First acknowledgment
    response1 = auth_client.post(url, [{"message": message_id}])
    assert response1.status_code == status.HTTP_200_OK
    assert DirectMessageAck.objects.filter(user=user, message_id=message_id).exists()

    # Second acknowledgment should not duplicate entries
    response2 = auth_client.post(url, [{"message": message_id}])
    assert response2.status_code == status.HTTP_200_OK
    assert DirectMessageAck.objects.filter(user=user, message_id=message_id).count() == 1


@pytest.mark.django_db
def test_ack_direct_messages_empty_list(auth_client, direct_thread):
    user = direct_thread.users.first()
    auth_client.force_authenticate(user)
    url = reverse("directmessage-ack-messages", kwargs={"thread_id": direct_thread.id})

    response = auth_client.post(url, data=[])
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_ack_direct_messages_unauthorized(client, direct_thread, direct_messages):
    url = reverse("directmessage-ack-messages", kwargs={"thread_id": direct_thread.id})

    message_ids = [msg.id for msg in direct_messages[:2]]
    response = client.post(url, data=[{"message": msg_id} for msg_id in message_ids])

    assert response.status_code == status.HTTP_403_FORBIDDEN
