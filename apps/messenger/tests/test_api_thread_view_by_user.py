from uuid import uuid4

import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
def test_thread_view_by_user_with_common_threads(
    make_auth_client, make_user, make_project, make_task, make_thread, make_message
):
    user1 = make_user()
    user2 = make_user()
    auth_client = make_auth_client(user=user1)
    project = make_project(owner=user1, members=[user2])
    task = make_task(project=project, owner=user1, members=[user1, user2])
    thread = make_thread(task=task)

    make_message(thread=thread, sender=user1)
    make_message(thread=thread, sender=user2)

    url = reverse("thread-by-user", kwargs={"user_id": user2.id})
    response = auth_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert len(response_data) == 1
    assert response_data[0]["unread_count"] == 2
    assert response_data[0]["project"]["id"] == str(project.id)
    assert response_data[0]["task"]["id"] == str(task.id)
    assert response_data[0]["type"] == "task"
    assert response_data[0]["name"] == task.title
    assert response_data[0]["thread"] == str(thread.id)


@pytest.mark.django_db
def test_thread_view_by_user_no_common_threads(make_auth_client, make_user, make_project, make_task, make_thread):
    user1 = make_user()
    user2 = make_user()
    auth_client = make_auth_client(user=user1)
    project = make_project(owner=user1)
    task = make_task(project=project)
    make_thread(task=task)

    url = reverse("thread-by-user", kwargs={"user_id": user2.id})
    response = auth_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert len(response_data) == 0


@pytest.mark.django_db
def test_thread_view_by_user_self_request(make_auth_client, make_user):
    user = make_user()
    auth_client = make_auth_client(user=user)

    url = reverse("thread-by-user", kwargs={"user_id": user.id})
    response = auth_client.get(url)

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_thread_view_by_user_invalid_user(make_auth_client, make_user):
    user = make_user()
    auth_client = make_auth_client(user=user)

    url = reverse("thread-by-user", kwargs={"user_id": str(uuid4())})
    response = auth_client.get(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND
