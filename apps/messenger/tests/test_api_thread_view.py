from uuid import uuid4

import pytest
from django.urls import reverse
from rest_framework import status

from apps.messenger.models import Message


@pytest.mark.django_db
def test_thread_view_get_messages(make_auth_client, make_user, make_project, make_task, make_thread, make_message):
    user = make_user()
    auth_client = make_auth_client(user=user)
    project = make_project(owner=user)
    task = make_task(project=project, members=[user])
    thread = make_thread(task=task)
    message1 = make_message(thread=thread, sender=user)
    message2 = make_message(thread=thread, sender=user)

    url = reverse("thread", kwargs={"thread_id": thread.id})
    response = auth_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert len(response_data["results"]) == 2
    assert response_data["results"][0]["content"] == message1.content
    assert response_data["results"][1]["content"] == message2.content


@pytest.mark.django_db
def test_thread_view_post_message(make_auth_client, make_user, make_project, make_task, make_thread):
    user = make_user()
    auth_client = make_auth_client(user=user)
    project = make_project(owner=user)
    task = make_task(project=project, members=[user])
    thread = make_thread(task=task)

    url = reverse("thread", kwargs={"thread_id": thread.id})
    payload = {"content": "New message"}
    response = auth_client.post(url, data=payload)

    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert response_data["content"] == "New message"
    assert response_data["sender"]["id"] == str(user.id)
    assert Message.objects.filter(thread=thread, content="New message").exists()


@pytest.mark.django_db
def test_thread_view_permission_denied(make_auth_client, make_user, make_project, make_task, make_thread):
    user = make_user()
    other_user = make_user()
    auth_client = make_auth_client(user=other_user)
    project = make_project(owner=user)
    task = make_task(project=project)
    thread = make_thread(task=task)

    url = reverse("thread", kwargs={"thread_id": thread.id})
    response = auth_client.get(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_thread_view_thread_not_found(make_auth_client, make_user):
    user = make_user()
    auth_client = make_auth_client(user=user)

    url = reverse("thread", kwargs={"thread_id": str(uuid4())})
    response = auth_client.get(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND
