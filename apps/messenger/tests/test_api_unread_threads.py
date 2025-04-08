import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
def test_unread_threads_view(
    make_auth_client, make_user, make_project, make_task, make_thread, make_message, make_thread_ack
):
    user = make_user()
    other_user = make_user()
    auth_client = make_auth_client(user=user)
    project = make_project(owner=user, members=[other_user])
    thread = make_thread(project=project)

    make_message(thread=thread, sender=user)
    make_message(thread=thread, sender=other_user)
    make_thread_ack(thread=thread, user=user)
    message = make_message(thread=thread, sender=other_user)

    url = reverse("unread-threads")
    response = auth_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert len(response_data) == 1
    assert response_data[0]["unread_count"] == 1
    assert response_data[0]["project"]["id"] == str(project.id)
    assert response_data[0]["task"] is None
    assert response_data[0]["type"] == "project"
    assert response_data[0]["name"] == project.title
    assert response_data[0]["last_unread_message_date"] == message.created_at.isoformat().replace("+00:00", "Z")


@pytest.mark.django_db
def test_unread_threads_view_with_task(
    make_auth_client, make_user, make_project, make_task, make_thread, make_message, make_thread_ack
):
    user = make_user()
    other_user = make_user()
    auth_client = make_auth_client(user=user)
    project = make_project(owner=user, members=[other_user])
    task = make_task(project=project, owner=user)
    thread = make_thread(task=task)

    make_message(thread=thread, sender=user)
    make_message(thread=thread, sender=other_user)
    make_thread_ack(thread=thread, user=user)
    message = make_message(thread=thread, sender=other_user)

    url = reverse("unread-threads")
    response = auth_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert len(response_data) == 1
    assert response_data[0]["unread_count"] == 1
    assert response_data[0]["project"]["id"] == str(project.id)
    assert response_data[0]["task"]["id"] == str(task.id)
    assert response_data[0]["type"] == "task"
    assert response_data[0]["name"] == task.title
    assert response_data[0]["last_unread_message_date"] == message.created_at.isoformat().replace("+00:00", "Z")
