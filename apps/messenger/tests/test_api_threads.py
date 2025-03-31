import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from apps.messenger.models import Thread, ThreadAck
from core.models import TaskAccess


@pytest.mark.django_db
def test_create_thread(make_auth_client, make_user, make_project):
    user = make_user()
    project = make_project(owner=user)
    auth_client = make_auth_client(user=user)
    payload = {"project": str(project.id)}
    response = auth_client.post(reverse("thread-list"), payload)

    assert response.status_code == status.HTTP_201_CREATED
    thread = Thread.objects.get(id=response.data["id"])
    assert thread.project_id == project.id
    assert thread.user.id == user.id


@pytest.mark.django_db
def test_user_threads(make_user, make_auth_client, make_project, make_thread):
    user = make_user()
    project = make_project(owner=user)
    auth_client = make_auth_client(user=user)
    make_thread(user=user, project=project)
    response = auth_client.get(reverse("thread-list"))
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) > 0


@pytest.mark.django_db
def test_cannot_see_other_threads(make_user, make_auth_client, make_project, make_thread):
    user = make_user()
    project = make_project(owner=user)
    auth_client = make_auth_client(user=user)
    make_thread(user=user, project=project)
    different_thread = make_thread()
    response = auth_client.get(reverse("thread-list"))
    assert response.status_code == status.HTTP_200_OK
    assert response.data["results"]
    assert different_thread.id not in [t["id"] for t in response.data["results"]]


@pytest.mark.django_db
def test_unread_count_api(make_user, make_auth_client, make_project, make_thread, make_message):
    user = make_user()
    other_user = make_user()
    project = make_project(owner=user, members=[other_user])
    auth_client = make_auth_client(user=user)
    thread = make_thread(user=user, project=project)
    make_message(thread=thread, sender=user)
    url = reverse("thread-list")
    response = auth_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["results"][0]["unread_count"] == 0

    auth_client.force_authenticate(other_user)
    response = auth_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["results"][0]["unread_count"] == 1


@pytest.mark.django_db
def test_unread_count_api_when_message_was_ack(make_user, make_auth_client, make_project, make_thread):
    user = make_user()
    auth_client = make_auth_client(user=user)
    project = make_project(owner=user)
    make_thread(user=user, project=project)
    url = reverse("thread-list")
    response = auth_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["results"][0]["unread_count"] == 0


@pytest.mark.django_db
def test_ack_direct_thread(make_user, make_auth_client, make_project, make_thread):
    user = make_user()
    auth_client = make_auth_client(user=user)
    project = make_project(owner=user)
    thread = make_thread(project=project, user=user)
    assert ThreadAck.objects.count() == 0
    url = reverse("thread-ack", args=[thread.id])
    seen_at = timezone.now()
    response = auth_client.post(url, {"seen_at": seen_at}, format="json")
    assert response.status_code == status.HTTP_200_OK
    assert ThreadAck.objects.count() == 1
    thread_ack = ThreadAck.objects.first()
    assert thread_ack.user == user
    assert thread_ack.seen_at == seen_at


def test_thread_filtering_by_project_id(make_user, make_auth_client, make_project, make_thread):
    user = make_user()
    auth_client = make_auth_client(user=user)
    project = make_project(owner=user)
    project2 = make_project(owner=user)
    make_thread(user=user, project=project)
    url = reverse("thread-list")
    response = auth_client.get(f"{url}?project_ids={project.id},{project2.id}")

    assert response.status_code == status.HTTP_200_OK
    results = response.json()["results"]
    assert len(results) == 1
    result_thread = results[0]
    assert result_thread["project"] == str(project.id)


def test_thread_filtering_by_task_id(make_user, make_auth_client, make_task, make_thread):
    user = make_user()
    auth_client = make_auth_client(user=user)
    task = make_task(owner=user)
    make_thread(user=user, task=task)
    url = reverse("thread-list")
    response = auth_client.get(f"{url}?task_ids={task.id}")

    assert response.status_code == status.HTTP_200_OK
    results = response.json()["results"]
    assert len(results) == 1
    thread = results[0]
    assert thread["task"] == str(task.id)


def test_thread_filtering_by_project_and_task_ids(make_auth_client, make_user, make_thread, make_task, make_project):
    user = make_user()
    auth_client = make_auth_client(user=user)
    task = make_task(owner=user)
    project = make_project(owner=user)
    project2 = make_project(owner=user)
    make_thread(user=user, project=project)
    make_thread(user=user, task=task)
    url = reverse("thread-list")
    project_ids = ",".join([str(project.id), str(project2.id)])
    task_ids = ",".join([str(task.id)])
    response = auth_client.get(f"{url}?project_ids={project_ids}&task_ids={task_ids}")

    assert response.status_code == status.HTTP_200_OK
    results = response.json()["results"]
    assert len(results) == 2
    thread1, thread2 = results
    if thread1["project"]:
        project_thread = thread1
        task_thread = thread2
    else:
        project_thread = thread2
        task_thread = thread1

    assert {project_thread["project"], task_thread["task"]} == {str(project.id), str(task.id)}


@pytest.mark.django_db
def test_retrieve_thread(make_auth_client, make_user, make_thread):
    user = make_user()
    auth_client = make_auth_client(user=user)
    thread = make_thread(user=user)
    url = reverse("thread-detail", args=[str(thread.id)])
    response = auth_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == str(thread.id)


@pytest.mark.django_db
def test_retrieve_thread_not_found(make_auth_client):
    auth_client = make_auth_client()
    url = reverse("thread-detail", args=[999])
    response = auth_client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND
