from collections import defaultdict
from datetime import datetime, timezone

from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import ProjectAccess, TaskAccess, User
from core.utils.websockets import WebsocketHelper

from .models import Message, Thread, ThreadAck
from .serializers import (
    MessageSerializer,
    MessengerProjectSerializer,
    MessengerTaskSerializer,
    MessengerUserSerializer,
    UnreadThreadSerializer,
    UserThreadsSerializer,
)


class PaginatedResponseMixin:
    def paginate_queryset(self, queryset):
        paginator = PageNumberPagination()
        paginator.page_size = 10  # Default page size
        paginated_queryset = paginator.paginate_queryset(queryset, self.request)
        return paginated_queryset, paginator

    def get_paginated_response(self, data, paginator):
        return paginator.get_paginated_response(data)


class UserThreadsMixin:
    def _get_threads_for_user(self, user):
        accessible_project_ids_qs = ProjectAccess.objects.filter(user=user)
        accessible_task_ids_qs = TaskAccess.objects.filter(user=user)
        accessible_project_ids = accessible_project_ids_qs.values_list("project_id", flat=True)
        accessible_task_ids = accessible_task_ids_qs.values_list("task_id", flat=True)

        return Thread.objects.filter(Q(project_id__in=accessible_project_ids) | Q(task_id__in=accessible_task_ids))


class UserThreadsView(APIView, UserThreadsMixin, PaginatedResponseMixin):
    serializer_class = UserThreadsSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        # Get all threads and direct threads of the user
        min_utc_aware = datetime.min.replace(tzinfo=timezone.utc)
        response_data = defaultdict(
            lambda: {"unread_count": 0, "last_unread_message_date": datetime.min.replace(tzinfo=timezone.utc)},
        )

        threads = self._get_threads_for_user(user)
        for thread in threads.all():
            thread_ack = ThreadAck.objects.filter(thread=thread.id, user=user).order_by("-created_at").first()
            seen_at = thread_ack.seen_at if thread_ack else min_utc_aware
            messages = thread.messages.filter(created_at__gte=seen_at)
            for message in messages.all():
                response_data[message.sender]["unread_count"] += 1
                response_data[message.sender]["last_unread_message_date"] = max(
                    response_data[message.sender]["last_unread_message_date"],
                    message.created_at,
                )

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


class UnreadThreadsView(APIView, UserThreadsMixin):
    serializer_class = UnreadThreadSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        # Get all threads and direct threads of the user
        min_utc_aware = datetime.min.replace(tzinfo=timezone.utc)
        response_data = []

        threads = self._get_threads_for_user(user)
        for thread in threads.all():
            thread_ack = ThreadAck.objects.filter(thread=thread.id, user=user).order_by("-created_at").first()
            seen_at = thread_ack.seen_at if thread_ack else min_utc_aware
            messages = thread.messages.filter(created_at__gte=seen_at).exclude(sender=user).order_by("-created_at")
            if not messages.exists():
                continue

            response_data.append(
                {
                    "unread_count": messages.count(),
                    "project": MessengerProjectSerializer(thread.project or thread.task.project).data,
                    "task": MessengerTaskSerializer(thread.task).data if thread.task else None,
                    "type": "project" if thread.project else "task",
                    "name": thread.project.title if thread.project else thread.task.title,
                    "last_unread_message_date": messages.first().created_at,
                    "thread": str(thread.id),
                }
            )

        sorted_response_data = sorted(response_data, key=lambda item: item["last_unread_message_date"], reverse=True)
        return Response(sorted_response_data, status=status.HTTP_200_OK)


class ThreadViewByUser(APIView, UserThreadsMixin):
    permission_classes = [IsAuthenticated]
    serializer_class = UnreadThreadSerializer

    def get(self, request, user_id, *args, **kwargs):
        requester = request.user
        thread_user = get_object_or_404(User, id=user_id)
        if thread_user == requester:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        requester_threads_qs = self._get_threads_for_user(requester)
        user_threads_qs = self._get_threads_for_user(thread_user)
        common_threads_qs = requester_threads_qs & user_threads_qs
        min_utc_aware = datetime.min.replace(tzinfo=timezone.utc)
        response_data = []
        for thread in common_threads_qs.iterator():
            thread_ack = ThreadAck.objects.filter(thread=thread.id, user=requester).order_by("-created_at").first()
            seen_at = thread_ack.seen_at if thread_ack else min_utc_aware
            messages = thread.messages.filter(created_at__gte=seen_at)
            response_data.append(
                {
                    "unread_count": messages.count(),
                    "project": MessengerProjectSerializer(thread.project or thread.task.project).data,
                    "task": MessengerTaskSerializer(thread.task).data if thread.task else None,
                    "type": "project" if thread.project else "task",
                    "name": thread.project.title if thread.project else thread.task.title,
                    "thread": str(thread.id),
                }
            )

        sorted_response_data = sorted(response_data, key=lambda item: item["unread_count"], reverse=True)
        return Response(sorted_response_data, status=status.HTTP_200_OK)


class ThreadView(APIView, UserThreadsMixin, PaginatedResponseMixin):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination

    def _get_thread(self, thread_id):
        thread = get_object_or_404(Thread, id=thread_id)
        user_threads = self._get_threads_for_user(self.request.user)

        if not user_threads.filter(id=thread.id).exists():
            raise PermissionDenied("You do not have permission to access this thread.")

        return thread

    def get(self, request, thread_id, *args, **kwargs):
        thread = self._get_thread(thread_id)
        messages = Message.objects.filter(thread=thread)

        paginated_messages, paginator = self.paginate_queryset(messages)
        serializer = self.serializer_class(paginated_messages, many=True)
        return self.get_paginated_response(serializer.data, paginator)

    def post(self, request, thread_id, *args, **kwargs):
        user = request.user
        thread = self._get_thread(thread_id)

        data = request.data.copy()
        data["thread"] = thread.id
        data["sender"] = user.id
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            message = serializer.save(sender=user)
            self._send_message_to_channel(message, thread)
            self._create_thread_ack(thread, user)
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

    def _create_thread_ack(self, thread, user):
        ThreadAck.objects.create(thread=thread, user=user, seen_at=datetime.now(timezone.utc))
