import pytest
from django.urls import reverse

from apps.messenger.models import MessageAck


@pytest.mark.django_db
def test_ack_messages_success(client, create_thread_with_messages):
    user1, _, _, messages = create_thread_with_messages()
    client.force_authenticate(user1)
    url = reverse("ack-messages")

    message_ids = [msg.id for msg in messages[:2]]
    response = client.post(url, data={"message_ids": message_ids})
    print(response.json())

    assert response.status_code == 200
    assert MessageAck.objects.filter(user=user1, message_id__in=message_ids).count() == 2


@pytest.mark.django_db
def test_ack_messages_idempotency(client, create_thread_with_messages):
    user1, _, _, messages = create_thread_with_messages()
    client.force_authenticate(user1)
    url = reverse("ack-messages")

    message_id = messages[0].id

    # First acknowledgment
    response1 = client.post(url, {"message_ids": [message_id]})
    assert response1.status_code == 200
    assert MessageAck.objects.filter(user=user1, message_id=message_id).exists()

    # Second acknowledgment should not duplicate entries
    response2 = client.post(url, {"message_ids": [message_id]})
    assert response2.status_code == 200
    assert MessageAck.objects.filter(user=user1, message_id=message_id).count() == 1


@pytest.mark.django_db
def test_ack_messages_empty_list(client, create_thread_with_messages):
    user1, _, _, _ = create_thread_with_messages()
    client.force_authenticate(user1)
    url = reverse("ack-messages")

    response = client.post(url, data={"message_ids": []})
    assert response.status_code == 400
    assert response.json() == {"message_ids": ["This field is required."]}


@pytest.mark.django_db
def test_ack_messages_unauthorized(client, create_thread_with_messages):
    _, _, _, messages = create_thread_with_messages()
    url = reverse("ack-messages")

    message_ids = [msg.id for msg in messages[:2]]
    response = client.post(url, data={"message_ids": message_ids})

    assert response.status_code == 401
