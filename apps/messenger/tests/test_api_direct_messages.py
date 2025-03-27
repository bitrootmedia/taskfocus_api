import pytest
from django.urls import reverse
from rest_framework import status


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
    assert response.status_code == status.HTTP_403_FORBIDDEN
