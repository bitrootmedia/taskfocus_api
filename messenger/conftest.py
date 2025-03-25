from uuid import uuid4

import pytest
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from core.models import User, Project, ProjectAccess
from messenger.models import Thread, Message, MessageAck


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", password="password")


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
def project(db, user):
    p = Project.objects.create(
        title="test-project",
        description="Test project",
        background_image="project_background/test.jpg",
        owner=user,
    )
    ProjectAccess.objects.create(project=p, user=user)
    return p


@pytest.fixture
def thread(db, user, project):
    return Thread.objects.create(project_id=project.id, user=user)


@pytest.fixture
def message(db, thread, user):
    return Message.objects.create(thread=thread, user=user, content="Test message")


@pytest.fixture
def message_ack(db, message, user):
    return MessageAck.objects.create(message=message, user=message.user)


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
            Message.objects.create(thread=thread, user=user1, content="Hello"),
            Message.objects.create(thread=thread, user=user2, content="Hi"),
            Message.objects.create(thread=thread, user=user1, content="How are you?"),
        ]
        return user1, user2, thread, messages

    return _create_thread_with_messages
