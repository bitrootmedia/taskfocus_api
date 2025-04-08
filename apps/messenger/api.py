from collections import defaultdict
from datetime import datetime, timezone

from django.db.models import Count, F, OuterRef, Q, Subquery, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from core.models import Project, ProjectAccess, Task, TaskAccess
from core.utils.websockets import WebsocketHelper

from .models import DirectMessage, DirectThread, DirectThreadAck, Message, Thread, ThreadAck
from .pagination import StandardResultsSetPagination
from .serializers import (
    DirectMessageSerializer,
    DirectThreadAckSerializer,
    DirectThreadSerializer,
    MessageSerializer,
    MessengerUserSerializer,
    ThreadAckSerializer,
    ThreadSerializer,
    UserThreadsSerializer,
)


class ThreadViewSet(ModelViewSet):
    serializer_class = ThreadSerializer
    ack_serializer_class = ThreadAckSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        accessible_project_ids_qs = ProjectAccess.objects.filter(user=user)
        accessible_task_ids_qs = TaskAccess.objects.filter(user=user)
        latest_seen_at_subquery = (
            ThreadAck.objects.filter(thread=OuterRef("id"), user=user).order_by("-created_at").values("seen_at")[:1]
        )

        project_filter = self.request.query_params.get("project_ids")
        task_filter = self.request.query_params.get("task_ids")

        if task_filter and not project_filter:
            accessible_project_ids_qs = accessible_project_ids_qs.none()

        if project_filter and not task_filter:
            accessible_task_ids_qs = accessible_task_ids_qs.none()

        if project_filter:
            project_filter = project_filter.split(",")
            accessible_project_ids_qs = accessible_project_ids_qs.filter(project_id__in=project_filter)

        if task_filter:
            task_filter = task_filter.split(",")
            accessible_task_ids_qs = accessible_task_ids_qs.filter(task_id__in=task_filter)

        accessible_project_ids = accessible_project_ids_qs.values_list("project_id", flat=True)
        accessible_task_ids = accessible_task_ids_qs.values_list("task_id", flat=True)
        filter_subquery = Q(messages__created_at__gt=F("last_seen_at")) & (~Q(messages__sender=user))
        min_utc_aware = datetime.min.replace(tzinfo=timezone.utc)
        return (
            Thread.objects.filter(Q(project_id__in=accessible_project_ids) | Q(task_id__in=accessible_task_ids))
            .annotate(
                last_seen_at=Coalesce(Subquery(latest_seen_at_subquery), Value(min_utc_aware)),
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
        min_utc_aware = datetime.min.replace(tzinfo=timezone.utc)
        queryset = (
            DirectThread.objects.filter(users=user)
            .annotate(
                last_seen_at=Coalesce(Subquery(latest_seen_at_subquery), Value(min_utc_aware)),
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

        users_set = set(data["users"])
        existing_thread = DirectThread.objects.filter(users__in=users_set).distinct()
        existing_thread = existing_thread.annotate(user_count=Count("users")).filter(user_count=len(users_set)).first()

        if existing_thread:
            thread = self.get_queryset().filter(id=existing_thread.id).first()
            return Response(self.get_serializer(thread).data, status=status.HTTP_200_OK)

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


class UserThreadsView(APIView):
    serializer_class = UserThreadsSerializer
    permission_classes = [IsAuthenticated]

    def _get_threads_for_user(self, user):
        accessible_project_ids_qs = ProjectAccess.objects.filter(user=user)
        accessible_task_ids_qs = TaskAccess.objects.filter(user=user)
        accessible_project_ids = accessible_project_ids_qs.values_list("project_id", flat=True)
        accessible_task_ids = accessible_task_ids_qs.values_list("task_id", flat=True)

        return Thread.objects.filter(Q(project_id__in=accessible_project_ids) | Q(task_id__in=accessible_task_ids))

    def _get_direct_threads_for_user(self, user):
        return DirectThread.objects.filter(users=user)

    def get(self, request, *args, **kwargs):
        user = request.user
        # Get all threads and direct threads of the user
        min_utc_aware = datetime.min.replace(tzinfo=timezone.utc)
        response_data = defaultdict(
            lambda: {"unread_count": 0, "threads": set(), "direct_threads": set()},
        )

        threads = self._get_threads_for_user(user)
        for thread in threads.all():
            thread_ack = ThreadAck.objects.filter(thread=thread.id, user=user).order_by("-created_at").first()
            seen_at = thread_ack.seen_at if thread_ack else min_utc_aware
            messages = thread.messages.filter(created_at__gte=seen_at)
            for message in messages.all():
                response_data[message.sender]["unread_count"] += 1
                response_data[message.sender]["threads"].add(thread.id)
                response_data[message.sender]["last_unread_message_date"] = max(
                    response_data[message.sender].get(
                        "last_unread_message_date", datetime.min.replace(tzinfo=timezone.utc)
                    ),
                    message.created_at,
                )

        # Below code should be uncomment when direct threads are implemented
        # direct_threads = self._get_direct_threads_for_user(user)
        # for direct_thread in direct_threads.all():
        #     thread_ack = (
        #         DirectThreadAck.objects.filter(thread=direct_thread.id, user=user).order_by("-created_at").first()
        #     )
        #     seen_at = thread_ack.seen_at if thread_ack else min_utc_aware
        #     messages = direct_thread.direct_messages.filter(created_at__gte=seen_at)
        #     for message in messages.all():
        #         response_data[message.sender]["unread_count"] += 1
        #         response_data[message.sender]["direct_threads"].add(direct_thread.id)

        response_data.pop(user, None)
        response_data = dict(response_data)
        sorted_response_data = dict(
            sorted(response_data.items(), key=lambda item: item[1]["unread_count"], reverse=True)
        )
        response_data = [
            {
                "user": MessengerUserSerializer(user).data,
                "unread_count": data["unread_count"],
                "last_unread_message_date": data["last_unread_message_date"],
            }
            for user, data in sorted_response_data.items()
        ]
        return Response(response_data)
