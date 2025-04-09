import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
def test_all_threads_view(make_auth_client, make_user, make_project, make_task, make_thread, make_message):
    user = make_user()
    another_user = make_user()
    auth_client = make_auth_client(user=user)
    project = make_project(owner=user)
    task = make_task(project=project, members=[user, another_user])
    thread1 = make_thread(project=project)
    thread2 = make_thread(task=task)

    make_message(thread=thread1, sender=another_user)
    make_message(thread=thread1, sender=another_user)
    make_message(thread=thread2, sender=another_user)

    url = reverse("all-threads")
    response = auth_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert len(response_data["results"]) == 2
    assert any(thread["thread"] == str(thread1.id) for thread in response_data["results"])
    assert any(thread["thread"] == str(thread2.id) for thread in response_data["results"])


@pytest.mark.django_db
def test_all_threads_view_no_threads(make_auth_client, make_user):
    user = make_user()
    auth_client = make_auth_client(user=user)

    url = reverse("all-threads")
    response = auth_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert len(response_data["results"]) == 0


@pytest.mark.django_db
def test_all_threads_view_pagination(make_auth_client, make_user, make_project, make_thread):
    user = make_user()
    auth_client = make_auth_client(user=user)
    project = make_project(owner=user)

    [make_thread(project=project) for _ in range(15)]

    url = reverse("all-threads")
    response = auth_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert len(response_data["results"]) == 10
    print(response_data["results"][0])
    assert response_data["count"] == 15
    assert response_data["next"] is not None

    response = auth_client.get(response_data["next"])
    response_data = response.json()
    assert len(response_data["results"]) == 5
    assert response_data["next"] is None
