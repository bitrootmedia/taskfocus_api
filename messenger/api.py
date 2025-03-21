from django.db import models
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet
from rest_framework.response import Response
from rest_framework.decorators import action

from core.models import Project, Task
from core.utils.websockets import WebsocketHelper

from .models import Thread, Message
from .pagination import StandardResultsSetPagination
from .serializers import ThreadSerializer, MessageSerializer


class ThreadViewSet(ReadOnlyModelViewSet):
    serializer_class = ThreadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        accessible_project_ids = Project.objects.filter(permissions__user=user).values_list("id", flat=True)
        accessible_task_ids = Task.objects.filter(permissions__user=user).values_list("id", flat=True)
        return Thread.objects.filter(
            models.Q(project_id__in=accessible_project_ids) | models.Q(task_id__in=accessible_task_ids)
        ).distinct()

    @action(detail=False, methods=["get"])
    def user_threads(self, request):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class MessageViewSet(ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_thread_object(self):
        user = self.request.user
        thread_id = self.kwargs.get("thread_id")
        thread = get_object_or_404(Thread, id=thread_id)

        assert thread.project_id or thread.task_id, f"No project_id and task_id in thread {thread_id}"

        if thread.project_id and not Project.objects.filter(id=thread.project_id, permissions__user=user).exists():
            raise PermissionDenied("You do not have permission to access messages in this project.")
        elif thread.task_id and not Task.objects.filter(id=thread.task_id, permissions__user=user).exists():
            raise PermissionDenied("You do not have permission to access messages in this task.")

        return thread

    def get_queryset(self):
        thread = self.get_thread_object()
        return Message.objects.filter(thread=thread).order_by("-created_at")

    @action(detail=False, methods=["get"], url_path="unread-count")
    def unread_count(self, request, thread_id=None):
        user = request.user
        thread = self.get_thread_object()

        unread_count = Message.objects.filter(thread=thread).exclude(acks__user=user).count()
        return Response({"unread_count": unread_count})

    def create(self, request, *args, **kwargs):
        user = request.user
        thread = self.get_thread_object()

        data = request.data.copy()
        data["user"] = user.id
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            message = serializer.save(user=user)
            self._send_message_to_channel(message, thread)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def _send_message_to_channel(message, thread):
        ws = WebsocketHelper()
        ws.send(
            f"thread_{thread.id}",
            "message_added",
            data={"content": f"{message.content}", "user": f"{message.user.id}"},
        )