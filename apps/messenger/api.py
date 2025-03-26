from django.db import models
from django.db.models import Count, Exists, OuterRef, Q, Subquery, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet, ViewSet

from core.models import Project, Task
from core.utils.websockets import WebsocketHelper

from .models import DirectMessage, DirectMessageAck, DirectThread, Message, MessageAck, Thread
from .pagination import StandardResultsSetPagination
from .serializers import (
    DirectMessageAckSerializer,
    DirectMessageSerializer,
    DirectThreadSerializer,
    MessageAckSerializer,
    MessageSerializer,
    ThreadSerializer,
)


class ThreadViewSet(ReadOnlyModelViewSet):
    serializer_class = ThreadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        accessible_project_ids = Project.objects.filter(permissions__user=user).values_list("id", flat=True)
        accessible_task_ids = Task.objects.filter(permissions__user=user).values_list("id", flat=True)
        return (
            Thread.objects.filter(
                models.Q(project_id__in=accessible_project_ids) | models.Q(task_id__in=accessible_task_ids)
            )
            .annotate(unread_count=Count("messages", filter=~Q(messages__acks__user=user)))
            .distinct()
        )

    @action(detail=False, methods=["get"])
    def user_threads(self, request):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class MessageViewSet(ModelViewSet):
    serializer_class = MessageSerializer
    ack_serializer_class = MessageAckSerializer
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
        acked_messages = MessageAck.objects.filter(user=self.request.user, message_id=OuterRef("id"))
        return Message.objects.filter(thread=thread).annotate(seen=Exists(acked_messages)).order_by("-created_at")

    def create(self, request, *args, **kwargs):
        user = request.user
        thread = self.get_thread_object()

        data = request.data.copy()
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

    @action(detail=False, methods=["POST"])
    def ack(self, request, thread_id):
        """
        Marks multiple messages as seen by the current user.
        Expected payload: {"message_ids": [uuid1, uuid2, uuid3]}
        """
        user = request.user
        serializer = self.ack_serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        message_ids = serializer.validated_data["message_ids"]

        existing_acks = set(
            MessageAck.objects.filter(user=user, message_id__in=message_ids).values_list("message_id", flat=True)
        )

        new_acks = [MessageAck(user=user, message_id=msg_id) for msg_id in message_ids if msg_id not in existing_acks]

        MessageAck.objects.bulk_create(new_acks, ignore_conflicts=True)
        return Response({"status": "Messages acknowledged"}, status=status.HTTP_200_OK)


class DirectThreadViewSet(ReadOnlyModelViewSet):
    serializer_class = DirectThreadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = DirectThread.objects.filter(users=user)
        unseen_messages_count_subquery = (
            DirectMessage.objects.filter(thread_id=OuterRef("id"))
            .exclude(acks__user=user)
            .values("thread_id")
            .annotate(count=Count("id"))
            .values("count")
        )

        queryset = queryset.annotate(
            unseen_messages_count=Coalesce(Subquery(unseen_messages_count_subquery), Value(0))
        )

        return queryset

    # def list(self, request, *args, **kwargs):
    #     queryset = self.filter_queryset(self.get_queryset())
    #
    #     page = self.paginate_queryset(queryset)
    #     if page is not None:
    #         serializer = self.get_serializer(page, many=True)
    #         user = self.request.user
    #         for thread in page:
    #             unseen_count = Message.objects.filter(thread_id=thread.id).exclude(acks__user=user).count()
    #             thread["unseen_messages_count"] = unseen_count
    #
    #         return self.get_paginated_response(serializer.data)
    #
    #     serializer = self.get_serializer(queryset, many=True)
    #     return Response(serializer.data)


class DirectMessageViewSet(ModelViewSet):
    serializer_class = DirectMessageSerializer
    ack_serializer_class = DirectMessageAckSerializer
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

    @action(detail=False, methods=["post"], url_path="ack")
    def ack(self, request, thread_id):
        user = request.user
        serializer = self.ack_serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        message_ids = serializer.validated_data["message_ids"]

        existing_acks = set(
            DirectMessageAck.objects.filter(user=user, message_id__in=message_ids).values_list("message_id", flat=True)
        )

        new_acks = [
            DirectMessageAck(user=user, message_id=msg_id) for msg_id in message_ids if msg_id not in existing_acks
        ]

        DirectMessageAck.objects.bulk_create(new_acks, ignore_conflicts=True)
        return Response({"status": "Messages acknowledged"}, status=status.HTTP_200_OK)
