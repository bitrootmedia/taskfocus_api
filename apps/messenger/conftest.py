from datetime import datetime

import pytest
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from apps.messenger.models import DirectMessage, DirectThread, DirectThreadAck, Message, Thread, ThreadAck
from core.models import Project, ProjectAccess, Task, TaskAccess, User


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", password="password")


@pytest.fixture
def integration_user1(db):
    return User.objects.create_user(username="testuser1", password="password")


@pytest.fixture
def integration_user2(db):
    return User.objects.create_user(username="testuser2", password="password")


@pytest.fixture
def integration_user3(db):
    return User.objects.create_user(username="testuser3", password="password")


@pytest.fixture
def integration_user4(db):
    return User.objects.create_user(username="testuser4", password="password")


@pytest.fixture
def client():
    client = APIClient()
    return client


@pytest.fixture
def auth_client(client, user):
    client.force_authenticate(user=user)
    token, created = Token.objects.get_or_create(user=user)
    client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
    return client


@pytest.fixture
def project(db, user, other_user):
    p = Project.objects.create(
        title="test-project",
        description="Test project",
        background_image="project_background/test.jpg",
        owner=user,
    )
    ProjectAccess.objects.create(project=p, user=user)
    ProjectAccess.objects.create(project=p, user=other_user)
    return p


@pytest.fixture
def project2(db, user, other_user):
    p = Project.objects.create(
        title="test-project2",
        description="Test project",
        background_image="project_background/test.jpg",
        owner=user,
    )
    ProjectAccess.objects.create(project=p, user=user)
    ProjectAccess.objects.create(project=p, user=other_user)
    return p


@pytest.fixture
def project3(db, user, other_user):
    p = Project.objects.create(
        title="test-project3",
        description="Test project",
        background_image="project_background/test.jpg",
        owner=user,
    )
    ProjectAccess.objects.create(project=p, user=user)
    ProjectAccess.objects.create(project=p, user=other_user)
    return p


@pytest.fixture
def task(db, other_user):
    task = Task.objects.create(owner=other_user)
    TaskAccess.objects.create(task=task, user=other_user)
    return task


@pytest.fixture
def thread(db, user, project):
    return Thread.objects.create(project_id=project.id, user=user)


@pytest.fixture
def thread_on_task(db, user, task):
    return Thread.objects.create(task_id=task.id, user=user)


@pytest.fixture
def thread_ack(db, user, thread):
    return ThreadAck.objects.create(thread=thread, seen_at=datetime.now(), user=user)


@pytest.fixture
def message(db, thread, user):
    return Message.objects.create(thread=thread, sender=user, content="Test message")


@pytest.fixture
def create_users(db):
    def _create_users():
        user1 = User.objects.create_user(username="user1", password="password")
        user2 = User.objects.create_user(username="user2", password="password")
        return user1, user2

    return _create_users


@pytest.fixture
def create_thread_with_messages(db, create_users, thread, project):
    def _create_thread_with_messages():
        user1, user2 = create_users()
        ProjectAccess.objects.all().delete()
        ProjectAccess.objects.create(project=project, user=user1)
        ProjectAccess.objects.create(project=project, user=user2)

        messages = [
            Message.objects.create(thread=thread, sender=user1, content="Hello"),
            Message.objects.create(thread=thread, sender=user2, content="Hi"),
            Message.objects.create(thread=thread, sender=user1, content="How are you?"),
        ]
        return user1, user2, thread, messages

    return _create_thread_with_messages


@pytest.fixture
def other_user(db):
    return User.objects.create_user(username="otheruser", password="password")


@pytest.fixture
def no_thread_user(db):
    return User.objects.create_user(username="no_thread_user", password="password")


@pytest.fixture
def no_thread_user_auth_client(client, no_thread_user):
    client.force_authenticate(user=no_thread_user)
    token, created = Token.objects.get_or_create(user=no_thread_user)
    client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
    return client


@pytest.fixture
def direct_thread(db, user, other_user):
    direct_thread = DirectThread.objects.create()
    direct_thread.users.set([user, other_user])
    return direct_thread


@pytest.fixture
def direct_thread_ack(db, user, direct_thread):
    return DirectThreadAck.objects.create(thread=direct_thread, seen_at=datetime.now(), user=user)


@pytest.fixture
def direct_message(db, direct_thread, user):
    return DirectMessage.objects.create(thread=direct_thread, sender=user, content="Test message")
