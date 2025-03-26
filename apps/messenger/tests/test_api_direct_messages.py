import pytest
from django.urls import reverse
from rest_framework import status

from apps.messenger.conftest import message_ack
from apps.messenger.models import DirectMessage, DirectMessageAck, DirectThread
from core.models import User


@pytest.mark.django_db
def test_user_can_access_direct_messages(auth_client, direct_thread, direct_message):
    print(direct_thread.id)
    url = reverse("direct-messages-list", kwargs={"thread_id": str(direct_thread.id)})
    response = auth_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 1


@pytest.mark.django_db
def test_user_cannot_access_direct_messages_without_permission(auth_client, direct_thread, direct_message):
    direct_thread.users.all().delete()
    url = reverse("direct-messages-list", kwargs={"thread_id": str(direct_thread.id)})
    response = auth_client.get(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_user_can_create_direct_message(auth_client, direct_thread, user):
    url = reverse("direct-messages-list", kwargs={"thread_id": str(direct_thread.id)})
    data = {"content": "New direct message"}
    response = auth_client.post(url, data)
    print(response.json())
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["content"] == "New direct message"


@pytest.mark.django_db
def test_user_cannot_create_direct_message_without_permission(auth_client, direct_thread):
    direct_thread.users.all().delete()
    url = reverse("direct-messages-list", kwargs={"thread_id": str(direct_thread.id)})
    data = {"content": "New direct message"}
    response = auth_client.post(url, data)
    print(response.json())
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_ack_direct_messages_success(auth_client, direct_thread, direct_message):
    user = direct_thread.users.first()
    auth_client.force_authenticate(user)
    url = reverse("direct-messages-ack", kwargs={"thread_id": str(direct_thread.id)})
    message_ids = [str(direct_message.id)]
    response = auth_client.post(url, {"message_ids": message_ids})

    assert response.status_code == status.HTTP_200_OK
    assert DirectMessageAck.objects.filter(user=user, message_id__in=message_ids).count() == 1


@pytest.mark.django_db
def test_ack_direct_messages_idempotency(auth_client, direct_thread, direct_message):
    user = direct_thread.users.first()
    auth_client.force_authenticate(user)
    url = reverse("direct-messages-ack", kwargs={"thread_id": str(direct_thread.id)})

    message_id = str(direct_message.id)

    # First acknowledgment
    response1 = auth_client.post(url, {"message_ids": [message_id]})
    print(response1.json())
    assert response1.status_code == status.HTTP_200_OK
    assert DirectMessageAck.objects.filter(user=user, message_id=message_id).exists()

    # Second acknowledgment should not duplicate entries
    response2 = auth_client.post(url, {"message_ids": [message_id]})
    assert response2.status_code == status.HTTP_200_OK
    assert DirectMessageAck.objects.filter(user=user, message_id=message_id).count() == 1


@pytest.mark.django_db
def test_ack_direct_messages_empty_list(auth_client, direct_thread):
    user = direct_thread.users.first()
    auth_client.force_authenticate(user)
    url = reverse("direct-messages-ack", kwargs={"thread_id": str(direct_thread.id)})

    response = auth_client.post(url, {"message_ids": []})
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_ack_direct_messages_unauthorized(client, direct_thread, direct_message):
    url = reverse("direct-messages-ack", kwargs={"thread_id": str(direct_thread.id)})
    response = client.post(url, {"message_ids": [str(direct_message.id)]})
    assert response.status_code == status.HTTP_403_FORBIDDEN
