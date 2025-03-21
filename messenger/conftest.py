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
def client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def auth_client(client, user):
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
