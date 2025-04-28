import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
def test_message_search_view(make_auth_client, make_user, make_project, make_task, make_thread, make_message):
    # Create users and authenticate
    user = make_user()
    other_user = make_user()
    auth_client = make_auth_client(user=user)

    # Create project and task with access for both users
    project = make_project(owner=user, members=[other_user])
    task = make_task(project=project, members=[user, other_user])

    # Create threads
    project_thread = make_thread(project=project)
    task_thread = make_thread(task=task)

    # Create messages with specific content
    make_message(thread=project_thread, sender=user, content="This is a test message")
    make_message(thread=project_thread, sender=other_user, content="Another message without the keyword")
    make_message(thread=task_thread, sender=other_user, content="This is a test message in task thread")

    # Test search endpoint with query parameter
    url = reverse("message-search")
    response = auth_client.get(url, {"query": "test"})

    # Verify response
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 2  # Should find both messages with "test"

    print(response.data["results"][0])
    # Verify the response contains thread context information
    for message in response.data["results"]:
        assert "thread" in message
        assert "id" in message["thread"]
        assert "type" in message["thread"]
        assert "name" in message["thread"]

    # Test search with no results
    response = auth_client.get(url, {"query": "nonexistent"})
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 0

    # Test search without query parameter (should return all messages)
    response = auth_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 3  # Should return all messages
