from datetime import datetime

from django.db import models
from django.db.models import Count, F, OuterRef, Q, Subquery, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from core.models import Project, Task
from core.utils.websockets import WebsocketHelper

from .models import DirectMessage, DirectThread, DirectThreadAck, Message, Thread, ThreadAck
from .pagination import StandardResultsSetPagination
from .serializers import (
    DirectMessageSerializer,
    DirectThreadAckSerializer,
    DirectThreadSerializer,
    MessageSerializer,
    ThreadAckSerializer,
    ThreadSerializer,
)


class ThreadViewSet(ModelViewSet):
    serializer_class = ThreadSerializer
    ack_serializer_class = ThreadAckSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        accessible_project_ids = Project.objects.filter(permissions__user=user).values_list("id", flat=True)
        accessible_task_ids = Task.objects.filter(permissions__user=user).values_list("id", flat=True)
        latest_seen_at_subquery = (
            ThreadAck.objects.filter(thread=OuterRef("id"), user=user).order_by("-created_at").values("seen_at")[:1]
        )

        filter_subquery = Q(messages__created_at__gt=F("last_seen_at")) & (~Q(messages__sender=user))
        return (
            Thread.objects.filter(
                models.Q(project_id__in=accessible_project_ids) | models.Q(task_id__in=accessible_task_ids)
            )
            .annotate(
                last_seen_at=Coalesce(Subquery(latest_seen_at_subquery), Value(datetime.min)),
                unread_count=Count("messages", filter=filter_subquery, distinct=True),
            )
            .order_by("-created_at")
            .distinct()
        )

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data["user"] = request.user.id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        serializer.data["unread_count"] = 0
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="ack")
    def ack(self, request, pk=None):
        thread = self.get_object()
        user = request.user
        serializer = self.ack_serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        seen_at = serializer.validated_data["seen_at"]

        ThreadAck.objects.create(thread=thread, user=user, seen_at=seen_at)

        return Response(status=status.HTTP_200_OK)


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

    def create(self, request, *args, **kwargs):
        user = request.user
        thread = self.get_thread_object()

        data = request.data.copy()
        data["thread"] = thread.id
        data["sender"] = user.id
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            message = serializer.save(sender=user)
            self._send_message_to_channel(message, thread)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def _send_message_to_channel(message, thread):
        ws = WebsocketHelper()
        ws.send(
            f"thread_{thread.id}",
            "message_added",
            data={"content": f"{message.content}", "sender": f"{message.sender.id}"},
        )


class DirectThreadViewSet(ModelViewSet):
    serializer_class = DirectThreadSerializer
    ack_serializer_class = DirectThreadAckSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        latest_seen_at_subquery = (
            DirectThreadAck.objects.filter(thread=OuterRef("id"), user=user)
            .order_by("-created_at")
            .values("seen_at")[:1]
        )

        filter_subquery = Q(direct_messages__created_at__gt=F("last_seen_at")) & (~Q(direct_messages__sender=user))
        queryset = (
            DirectThread.objects.filter(users=user)
            .annotate(
                last_seen_at=Coalesce(Subquery(latest_seen_at_subquery), Value(datetime.min)),
                unread_count=Count(
                    "direct_messages",
                    filter=filter_subquery,
                    distinct=True,
                ),
            )
            .order_by("-created_at")
        )
        return queryset

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        if str(request.user.id) not in data["users"]:
            data["users"].append(str(request.user.id))

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        serializer.data["unread_count"] = 0
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="ack")
    def ack(self, request, pk=None):
        thread = self.get_object()
        user = request.user
        serializer = self.ack_serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        seen_at = serializer.validated_data["seen_at"]

        DirectThreadAck.objects.create(thread=thread, user=user, seen_at=seen_at)

        return Response(status=status.HTTP_200_OK)


class DirectMessageViewSet(ModelViewSet):
    serializer_class = DirectMessageSerializer
    permission_classes = [IsAuthenticated]

    def _get_thread(self, thread_id):
        thread = get_object_or_404(DirectThread, id=thread_id)
        if not thread.users.filter(id=self.request.user.id).exists():
            raise PermissionDenied("You do not have permission to access messages in this thread.")

        return thread

    def get_queryset(self):
        thread_id = self.kwargs.get("thread_id")
        thread = self._get_thread(thread_id)
        return DirectMessage.objects.filter(thread=thread).order_by("-created_at")

    @staticmethod
    def _send_message_to_channel(direct_message, direct_thread):
        ws = WebsocketHelper()
        ws.send(
            f"direct_thread_{direct_thread.id}",
            "message_added",
            data={"content": f"{direct_message.content}", "user": f"{direct_message.sender.id}"},
        )

    def create(self, request, *args, **kwargs):
        user = self.request.user
        data = request.data.copy()
        data["sender"] = user.id
        data["thread"] = self._get_thread(self.kwargs.get("thread_id")).id
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            direct_message = serializer.save()
            self._send_message_to_channel(direct_message, direct_message.thread)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
