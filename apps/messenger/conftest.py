from datetime import datetime
from uuid import uuid4

import pytest
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from apps.messenger.models import DirectMessage, DirectThread, DirectThreadAck, Message, Thread, ThreadAck
from core.models import Project, ProjectAccess, Task, TaskAccess, User


@pytest.fixture
def make_user(db):
    def _make_user(**kwargs):
        username = kwargs.pop("username", f"testuser-{uuid4()}")
        password = kwargs.pop("password", "password")
        return User.objects.create_user(username=username, password=password, **kwargs)

    return _make_user


@pytest.fixture
def make_project(db, make_user):
    def _make_project(**kwargs):
        if "owner" not in kwargs:
            kwargs["owner"] = make_user(username="owner", password="password")

        members = kwargs.pop("members", [])
        project = Project.objects.create(
            title=kwargs.pop("title", f"test-project-{uuid4()}"),
            description=kwargs.pop("description", "Test project"),
            **kwargs,
        )
        ProjectAccess.objects.create(project=project, user=kwargs["owner"])

        for member in members:
            ProjectAccess.objects.create(project=project, user=member)

        return project

    return _make_project


@pytest.fixture
def make_task(db, make_user):
    def _make_task(**kwargs):
        if "owner" not in kwargs:
            kwargs["owner"] = make_user(username="task_owner", password="password")
        task = Task.objects.create(**kwargs)
        TaskAccess.objects.create(task=task, user=kwargs["owner"])
        return task

    return _make_task


@pytest.fixture
def make_thread(db, make_user, make_project, make_task):
    def _make_thread(**kwargs):
        if "user" not in kwargs:
            kwargs["user"] = make_user()
        if "project" not in kwargs and "task" not in kwargs:
            kwargs["project"] = make_project(owner=kwargs["user"])

        return Thread.objects.create(**kwargs)

    return _make_thread


@pytest.fixture
def make_thread_ack(db, make_user, make_thread):
    def _make_thread_ack(**kwargs):
        if "user" not in kwargs:
            kwargs["user"] = make_user()
        if "thread" not in kwargs:
            kwargs["thread"] = make_thread()
        return ThreadAck.objects.create(seen_at=datetime.now(), **kwargs)

    return _make_thread_ack


@pytest.fixture
def make_message(db, make_user, make_thread):
    def _make_message(**kwargs):
        if "sender" not in kwargs:
            kwargs["sender"] = make_user()
        if "thread" not in kwargs:
            kwargs["thread"] = make_thread()
        return Message.objects.create(content="Test message", **kwargs)

    return _make_message


@pytest.fixture
def make_direct_thread(db, make_user):
    def _make_direct_thread(**kwargs):
        if "users" not in kwargs:
            kwargs["users"] = [
                make_user(),
                make_user(),
            ]
        direct_thread = DirectThread.objects.create()
        direct_thread.users.set(kwargs["users"])
        return direct_thread

    return _make_direct_thread


@pytest.fixture
def make_direct_thread_ack(db, make_user, make_direct_thread):
    def _make_direct_thread_ack(**kwargs):
        if "user" not in kwargs:
            kwargs["user"] = make_user()
        if "thread" not in kwargs:
            kwargs["thread"] = make_direct_thread()
        return DirectThreadAck.objects.create(seen_at=datetime.now(), **kwargs)

    return _make_direct_thread_ack


@pytest.fixture
def make_direct_message(db, make_user, make_direct_thread):
    def _make_direct_message(**kwargs):
        if "sender" not in kwargs:
            kwargs["sender"] = make_user()
        if "thread" not in kwargs:
            kwargs["thread"] = make_direct_thread()
        return DirectMessage.objects.create(content="Test message", **kwargs)

    return _make_direct_message


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def make_auth_client(make_user):
    def _auth_client(user=None):
        if user is None:
            user = make_user()
        client = APIClient()
        client.force_authenticate(user=user)
        token, created = Token.objects.get_or_create(user=user)
        client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
        return client

    return _auth_client
