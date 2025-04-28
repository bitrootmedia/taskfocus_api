from collections import defaultdict
from datetime import datetime, timezone

from django.db.models import DateTimeField, OuterRef, Q, Subquery
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import ProjectAccess, TaskAccess, User
from core.utils.websockets import WebsocketHelper

from .filters import MessageFilter
from .models import Message, Thread, ThreadAck
from .serializers import (
    MessageSerializer,
    MessengerProjectSerializer,
    MessengerTaskSerializer,
    MessengerUserSerializer,
    ThreadSerializer,
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

    def _get_threads_for_users(self, users: list[User]):
        accessible_project_ids_qs = ProjectAccess.objects.filter(user__in=users)
        accessible_task_ids_qs = TaskAccess.objects.filter(user__in=users)
        accessible_project_ids = list(set(accessible_project_ids_qs.values_list("project_id", flat=True)))
        accessible_task_ids = list(set(accessible_task_ids_qs.values_list("task_id", flat=True)))

        return Thread.objects.filter(Q(project_id__in=accessible_project_ids) | Q(task_id__in=accessible_task_ids))


class UserThreadsView(APIView, UserThreadsMixin, PaginatedResponseMixin):
    serializer_class = UserThreadsSerializer
    permission_classes = [IsAuthenticated]

    def _get_all_users_requester_can_chat_with(self, user):
        project_users = (
            ProjectAccess.objects.filter(
                project_id__in=ProjectAccess.objects.filter(user=user).values_list("project_id", flat=True)
            )
            .exclude(user=user)
            .values("user")
        )

        task_users = (
            TaskAccess.objects.filter(
                task_id__in=TaskAccess.objects.filter(user=user).values_list("task_id", flat=True)
            )
            .exclude(user=user)
            .values("user")
        )

        user_ids = set(project_users.values_list("user", flat=True)) | set(task_users.values_list("user", flat=True))
        return User.objects.filter(id__in=user_ids).distinct()

    def get(self, request, *args, **kwargs):
        user = request.user
        min_utc_aware = datetime.min.replace(tzinfo=timezone.utc)
        response_data = defaultdict(
            lambda: {"unread_count": 0, "last_unread_message_date": datetime.min.replace(tzinfo=timezone.utc)},
        )

        chat_users = self._get_all_users_requester_can_chat_with(user)
        chat_users_threads = self._get_threads_for_users(list(chat_users))

        for thread in chat_users_threads.prefetch_related("messages").all():
            thread_ack = ThreadAck.objects.filter(thread=thread.id, user=user).order_by("-created_at").first()
            seen_at = thread_ack.seen_at if thread_ack else min_utc_aware
            for message in thread.messages.all():
                if message.created_at >= seen_at:
                    response_data[message.sender]["unread_count"] += 1
                    response_data[message.sender]["last_unread_message_date"] = max(
                        response_data[message.sender]["last_unread_message_date"],
                        message.created_at,
                    )
                else:
                    response_data[message.sender]["unread_count"] += 0

        for chat_user in chat_users:
            if chat_user not in response_data:
                response_data[chat_user] = {"unread_count": 0, "last_unread_message_date": None}

        response_data.pop(user, None)
        response_data = dict(response_data)
        sorted_response_data = dict(
            sorted(response_data.items(), key=lambda item: item[1]["unread_count"], reverse=True)
        )
        response_data = [
            {
                "user": MessengerUserSerializer(user).data,
                "unread_count": data["unread_count"],
                "last_unread_message_date": data["last_unread_message_date"] if data["unread_count"] > 0 else None,
            }
            for user, data in sorted_response_data.items()
        ]
        return Response(response_data)


class AllThreadsView(APIView, UserThreadsMixin, PaginatedResponseMixin):
    serializer_class = ThreadSerializer
    permission_classes = [IsAuthenticated]

    def _get_threads_for_user(self, user):
        latest_message_date = (
            Message.objects.filter(thread_id=OuterRef("pk")).order_by("-created_at").values("created_at")[:1]
        )

        return (
            super()
            ._get_threads_for_user(user)
            .prefetch_related("messages")
            .annotate(
                latest_message_created_at=Coalesce(
                    Subquery(latest_message_date, output_field=DateTimeField()),
                    datetime.min.replace(tzinfo=timezone.utc),
                )
            )
            .order_by("-latest_message_created_at")
        )

    def get(self, request, *args, **kwargs):
        threads = self._get_threads_for_user(request.user)
        paginated_threads, paginator = self.paginate_queryset(threads)

        user = request.user
        min_utc_aware = datetime.min.replace(tzinfo=timezone.utc)
        response_data = []
        for thread in paginated_threads:
            thread_ack = ThreadAck.objects.filter(thread=thread.id, user=user).order_by("-created_at").first()
            seen_at = thread_ack.seen_at if thread_ack else min_utc_aware
            messages = thread.messages.filter(created_at__gte=seen_at).exclude(sender=user).order_by("-created_at")
            recent_message = messages.first()
            thread_other_participants = [u for u in thread.participants if u != user]
            response_data.append(
                {
                    "unread_count": messages.count(),
                    "project": MessengerProjectSerializer(thread.project or thread.task.project).data,
                    "task": MessengerTaskSerializer(thread.task).data if thread.task else None,
                    "type": "project" if thread.project else "task",
                    "name": thread.project.title if thread.project else thread.task.title,
                    "last_unread_message_date": recent_message and recent_message.created_at,
                    "thread": str(thread.id),
                    "participants": MessengerUserSerializer(thread_other_participants, many=True).data,
                }
            )

        sorted_response_data = sorted(
            response_data, key=lambda item: item.get("last_unread_message_date") or min_utc_aware, reverse=True
        )
        return self.get_paginated_response(sorted_response_data, paginator)


class UnreadThreadsView(APIView, UserThreadsMixin):
    serializer_class = UnreadThreadSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        # Get all threads and direct threads of the user
        min_utc_aware = datetime.min.replace(tzinfo=timezone.utc)
        response_data = []

        threads = self._get_threads_for_user(user)
        for thread in threads.prefetch_related("messages").all():
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


class MessageSearchView(APIView, UserThreadsMixin, PaginatedResponseMixin):
    permission_classes = [IsAuthenticated]
    serializer_class = MessageSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = MessageFilter
    search_fields = ["content"]

    def get(self, request, *args, **kwargs):
        user_threads = self._get_threads_for_user(request.user)
        user_thread_ids = user_threads.values_list("id", flat=True)

        # Filter messages by those threads
        queryset = Message.objects.filter(thread_id__in=user_thread_ids)

        search_query = request.query_params.get("query", None)
        if search_query:
            queryset = queryset.filter(content__icontains=search_query)

        for backend in self.filter_backends:
            queryset = backend().filter_queryset(request, queryset, self)

        queryset = queryset.order_by("-created_at")
        paginated_queryset, paginator = self.paginate_queryset(queryset)

        response_data = []
        for message in paginated_queryset:
            thread = message.thread
            message_data = self.serializer_class(message).data
            message_data["thread"] = {
                "id": str(thread.id),
                "project": (
                    MessengerProjectSerializer(thread.project or (thread.task.project if thread.task else None)).data
                    if thread.project or thread.task
                    else None
                ),
                "task": MessengerTaskSerializer(thread.task).data if thread.task else None,
                "type": "project" if thread.project else "task",
                "name": thread.project.title if thread.project else (thread.task.title if thread.task else "Unknown"),
            }
            response_data.append(message_data)

        return self.get_paginated_response(response_data, paginator)
