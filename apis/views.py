import json
import pathlib
import time
import uuid
import mimetypes
from collections import defaultdict

from django.http import JsonResponse
from django.utils.text import slugify
from django.utils.timezone import now
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import OrderingFilter, SearchFilter
from django.core.files.storage import default_storage
from rest_framework.response import Response
from rest_framework.views import APIView
from core.utils.hashtags import extract_hashtags
from core.utils.notifications import create_notification_from_comment
from core.utils.time_from_seconds import time_from_seconds
from core.utils.permissions import user_can_see_task
from core.utils.websockets import WebsocketHelper
from .filters import (
    ProjectFilter,
    TaskFilter,
    LogFilter,
    CommentFilter,
    AttachmentFilter,
    TaskSessionFilter,
    ProjectAccessFilter,
    TaskAccessFilter,
    ReminderFilter,
    NotificationAckFilter,
    PrivateNoteFilter,
    NoteFilter,
)
from .serializers import (
    ProjectListSerializer,
    ProjectListReadOnlySerializer,
    ProjectDetailReadOnlySerializer,
    ProjectDetailSerializer,
    TaskListSerializer,
    TaskDetailSerializer,
    LogListSerializer,
    CommentListSerializer,
    TaskSessionListSerializer,
    CommentListReadOnlySerializer,
    CommentDetailSerializer,
    AttachmentListSerializer,
    AttachmentDetailSerializer,
    ProjectAccessSerializer,
    TaskTotalTimeReadOnlySerializer,
    UserSerializer,
    ProjectAccessDetailSerializer,
    TaskSessionDetailSerializer,
    TaskReadOnlySerializer,
    TaskAccessDetailSerializer,
    TaskAccessSerializer,
    NotificationAckSerializer,
    UserTaskQueueSerializer,
    ReminderSerializer,
    ReminderReadOnlySerializer,
    PrivateNoteListSerializer,
    PrivateNoteDetailSerializer,
    TaskBlockListSerializer,
    TaskBlockDetailSerializer,
    PinDetailSerializer,
    WorkSessionsBreakdownInputSerializer,
    WorkSessionsWSBSerializer,
    NoteListSerializer,
    NoteDetailSerializer,
)

from core.models import (
    Project,
    Task,
    Log,
    Comment,
    Attachment,
    ProjectAccess,
    User,
    TaskWorkSession,
    TaskAccess,
    NotificationAck,
    UserTaskQueue,
    Reminder,
    Notification,
    Team,
    PrivateNote,
    TaskBlock,
    Pin,
    Note,
)
from django.db.models import Q, F, Sum
from .permissions import (
    HasProjectAccess,
    HasTaskAccess,
    IsAuthorOrReadOnly,
    IsOwnerOrReadOnly,
    IsProjectOwner,
    IsTaskOwner,
    IsPrivateNoteOwner,
    BlockUserHasTaskAccess,
)


class UserList(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]

    def get_queryset(self):
        user_teams = Team.objects.filter(user=self.request.user)
        users = User.objects.filter(teams__in=user_teams).distinct()

        return users


class UserDetail(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()

    def get_serializer_class(self):
        return UserSerializer


class ProjectList(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = ProjectFilter

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ProjectListReadOnlySerializer

        return ProjectListSerializer

    def get_queryset(self):
        user = self.request.user

        if self.request.GET.get("user"):
            user = User.objects.get(pk=self.request.GET.get("user"))

        projects = (
            Project.objects.filter(Q(owner=user) | Q(permissions__user=user))
            .distinct()
            .order_by("created_at")
        )
        return projects

    def perform_create(self, serializer):
        project = serializer.save(owner=self.request.user)
        Log.objects.create(
            project=project, user=self.request.user, message="Project created"
        )


class ProjectDetail(generics.RetrieveUpdateAPIView):
    permission_classes = (HasProjectAccess,)
    queryset = Project.objects.all()

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ProjectDetailReadOnlySerializer

        return ProjectDetailSerializer

    def perform_update(self, serializer):
        project = serializer.save()
        Log.objects.create(
            project=project, user=self.request.user, message="Project updated"
        )


class TaskList(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TaskListSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = TaskFilter

    def get_serializer_class(self):
        if self.request.method == "GET":
            return TaskReadOnlySerializer
        else:
            return TaskListSerializer

    def get_queryset(self):
        user = self.request.user
        if self.request.GET.get("user"):
            user = User.objects.get(pk=self.request.GET.get("user"))

        tasks = (
            Task.objects.filter(
                Q(owner=user)
                | Q(permissions__user=user)
                | Q(project__owner=user)
                | Q(project__permissions__user=user)
            )
            .distinct()
            .order_by("position")
        )

        return tasks

    def perform_create(self, serializer):
        task = serializer.save(
            owner=self.request.user, responsible=self.request.user
        )
        hashtags = extract_hashtags(task.title)
        if hashtags:
            task.tag = ",".join(hashtags)
            task.save()

        add_to_user_queue = self.request.data.get("add_to_user_queue", False)

        if add_to_user_queue:
            queue_position = self.request.data.get("queue_position", "top")
            priority = 100
            if queue_position == "top":
                utq = (
                    UserTaskQueue.objects.filter(user=self.request.user)
                    .order_by("-priority")
                    .first()
                )
                if utq:
                    priority = utq.priority + 10

            if queue_position == "bottom":
                utq = (
                    UserTaskQueue.objects.filter(user=self.request.user)
                    .order_by("priority")
                    .first()
                )
                if utq:
                    priority = utq.priority - 10

            UserTaskQueue.objects.create(
                user=self.request.user, task=task, priority=priority
            )

        TaskAccess.objects.create(task=task, user=self.request.user)

        Log.objects.create(
            task=task, user=self.request.user, message="Task created"
        )


class TaskDetail(generics.RetrieveUpdateAPIView):
    serializer_class = TaskDetailSerializer
    permission_classes = (HasTaskAccess,)
    queryset = Task.objects.all()

    def get_serializer_class(self):
        if self.request.method == "GET":
            return TaskReadOnlySerializer
        return TaskDetailSerializer

    def perform_update(self, serializer):
        instance = self.get_object()
        previous_data = Task.objects.get(pk=instance.pk)
        task = serializer.save()

        fields_to_check = [
            "project",
            "status",
            "eta_date",
            "estimated_work_hours",
            "progress",
            "is_urgent",
        ]

        for field in fields_to_check:
            new_value = getattr(task, field)
            old_value = getattr(previous_data, field)
            if new_value != old_value:
                Log.objects.create(
                    task=task,
                    user=self.request.user,
                    message=f"Task updated by {self.request.user.username}. "
                    f"{field} changed from {old_value} to {new_value}",
                )

        if (
            task.responsible != previous_data.responsible
            and task.responsible is not None
            and self.request.user != task.responsible
        ):
            Log.objects.create(
                task=task,
                user=self.request.user,
                message=f"Responsible person changed to {task.responsible}",
            )

            utq = UserTaskQueue.objects.filter(
                user=task.responsible, task=task
            )
            if not utq:
                UserTaskQueue.objects.create(
                    user=task.responsible, task=task, priority=int(time.time())
                )

            notification = Notification.objects.create(
                task=task,
                project=task.project,
                content=f"You are now responsible for task [{task.title}] (set by {self.request.user.username})",
            )

            NotificationAck.objects.create(
                notification=notification, user=task.responsible
            )


class TaskTotalTime(generics.RetrieveAPIView):
    permission_classes = (HasTaskAccess,)
    serializer_class = TaskTotalTimeReadOnlySerializer
    queryset = Task.objects.all()


class TaskBlockList(generics.ListCreateAPIView):
    serializer_class = TaskBlockListSerializer
    permission_classes = (IsAuthenticated,)

    def get_task(self):
        task_id = self.kwargs.get("pk")
        if not task_id:
            raise PermissionDenied()
        return Task.objects.get(pk=task_id)

    def has_task_access(self):
        # Make sure user has access to the task
        task = self.get_task()
        has_task_access = HasTaskAccess().has_object_permission(
            self.request, self, task
        )
        if not has_task_access:
            raise PermissionDenied()

        return True

    def get_queryset(self):
        self.has_task_access()
        task_id = self.kwargs.get("pk", None)
        blocks = (
            TaskBlock.objects.filter(task__id=task_id)
            .distinct()
            .order_by("position")
        )

        return blocks

    def perform_create(self, serializer):
        self.has_task_access()
        task = Task.objects.get(pk=self.kwargs["pk"])
        instance = serializer.save(created_by=self.request.user, task=task)
        # In theory new blocks will always be last but since API allows
        # to create a block with arbitrary position this is just a safeguard
        #
        # Increase position of all following blocks
        # (including the one we might be switching with)
        (
            TaskBlock.objects.filter(
                task=task,
                position__gte=instance.position,
            )
            .exclude(id=instance.id)
            .update(position=F("position") + 1)
        )
        Log.objects.create(
            task=task, user=self.request.user, message="User created a block"
        )


class TaskBlockDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TaskBlockDetailSerializer
    permission_classes = (BlockUserHasTaskAccess,)
    queryset = TaskBlock.objects.all()

    def perform_update(self, serializer):
        instance = serializer.save()
        # Increase position of all following blocks
        # (including the one we might be switching with)
        (
            TaskBlock.objects.filter(
                task=instance.task,
                position__gte=instance.position,
            )
            .exclude(id=instance.id)
            .update(position=F("position") + 1)
        )
        Log.objects.create(
            user=self.request.user,
            task=instance.task,
            message="Block updated",
        )

    def perform_destroy(self, instance):
        Log.objects.create(
            task=instance.task,
            user=self.request.user,
            message="Block deleted",
        )

        # Decrease position of all following blocks on delete.
        TaskBlock.objects.filter(
            task=instance.task, position__gt=instance.position
        ).update(position=F("position") - 1)

        instance.delete()


class LogList(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = LogListSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = LogFilter
    search_fields = ["message"]

    def get_queryset(self):
        return Log.objects.filter(
            Q(user=self.request.user)
            | Q(task__owner=self.request.user)
            | Q(task__permissions__user=self.request.user)
            | Q(project__owner=self.request.user)
            | Q(project__permissions__user=self.request.user)
        )


class TaskSessionDetail(generics.RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated,)

    def get_serializer_class(self):
        return TaskSessionDetailSerializer

    def get_queryset(self):
        queryset = TaskWorkSession.objects.filter(user=self.request.user)
        return queryset

    def perform_update(self, serializer):
        instance = self.get_object()
        previous_data = TaskWorkSession.objects.get(pk=instance.pk)
        tws = serializer.save()

        fields_to_check = [
            "started_at",
            "stopped_at",
        ]

        for field in fields_to_check:
            new_value = getattr(tws, field)
            old_value = getattr(previous_data, field)
            if new_value != old_value:
                Log.objects.create(
                    task=instance.task,
                    user=self.request.user,
                    message=f"TaskWorkSession updated by {self.request.user.username}. "
                    f"{field} changed from {old_value} to {new_value}",
                )


class TaskSessionList(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TaskSessionListSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = TaskSessionFilter
    search_fields = ["title"]

    def get_queryset(self):
        work_sessions = (
            TaskWorkSession.objects.filter(
                Q(user=self.request.user)
                | Q(task__owner=self.request.user)
                | Q(task__permissions__user=self.request.user)
            )
            .distinct()
            .order_by("started_at")
        )
        return work_sessions


class CommentList(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CommentListSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = CommentFilter
    search_fields = ["content"]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return CommentListReadOnlySerializer
        else:
            return CommentListSerializer

    def get_queryset(self):
        comments = (
            Comment.objects.filter(
                Q(author=self.request.user)
                | Q(project__owner=self.request.user)
                | Q(project__permissions__user=self.request.user)
                | Q(task__permissions__user=self.request.user)
                | Q(task__owner=self.request.user)
            )
            .distinct()
            .order_by("-created_at")
        )
        return comments

    def perform_create(self, serializer):
        comment = serializer.save(author=self.request.user)
        if comment.task and comment.task.project and not comment.project:
            comment.project = comment.task.project
            comment.save()

        create_notification_from_comment(comment)


class CommentDetail(generics.RetrieveUpdateAPIView):
    serializer_class = CommentDetailSerializer
    permission_classes = (IsAuthorOrReadOnly,)
    queryset = Comment.objects.all()


class NoteList(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = NoteListSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = NoteFilter

    def get_queryset(self):
        notes = (
            Note.objects.filter(user=self.request.user)
            .distinct()
            .order_by("-created_at")
        )
        return notes

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class NoteDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = NoteDetailSerializer

    def get_queryset(self):
        return Note.objects.filter(user=self.request.user)


class PrivateNoteList(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = PrivateNoteListSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = PrivateNoteFilter

    def get_queryset(self):
        notes = PrivateNote.objects.filter(user=self.request.user)
        return notes

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)  # is this redundant?


class PrivateNoteDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsPrivateNoteOwner,)
    serializer_class = PrivateNoteDetailSerializer

    def get_queryset(self):
        queryset = PrivateNote.objects.filter(user=self.request.user)
        return queryset


class AttachmentList(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = AttachmentListSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = AttachmentFilter
    search_fields = ["title"]

    def get_queryset(self):
        attachments = (
            Attachment.objects.filter(
                Q(owner=self.request.user)
                | Q(project__owner=self.request.user)
                | Q(project__permissions__user=self.request.user)
                | Q(task__owner=self.request.user)
                | Q(task__permissions__user=self.request.user)
            )
            .distinct()
            .order_by("created_at")
        )
        return attachments

    def perform_create(self, serializer):
        attachment = serializer.save(owner=self.request.user)
        Log.objects.create(
            task=attachment.task,
            user=self.request.user,
            message=f"New attachment ({attachment.name}) to the task by {attachment.user}",
        )


class AttachmentDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AttachmentDetailSerializer
    permission_classes = (IsOwnerOrReadOnly,)
    queryset = Attachment.objects.all()


class ProjectAccessList(generics.ListCreateAPIView):
    # TODO: this needs reviewing + security checks
    permission_classes = (IsAuthenticated,)
    serializer_class = ProjectAccessSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = ProjectAccessFilter

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ProjectAccessDetailSerializer
        else:
            return ProjectAccessSerializer

    def get_queryset(self):
        project_accesses = ProjectAccess.objects.filter(
            Q(user=self.request.user) | Q(project__owner=self.request.user)
        ).order_by("id")
        return project_accesses

    def perform_create(self, serializer):
        if self.request.user != serializer.validated_data["project"].owner:
            raise PermissionDenied()
        serializer.save()

    # TODO: fix this - /api/schema is killed here
    # def get_permissions(self):
    #     if self.request.method != "GET":
    #         project = Project.objects.filter(
    #             id=self.request.POST.get("project")
    #         ).first()
    #         if not project or project.owner != self.request.user:
    #             raise PermissionDenied()
    #
    #     return super().get_permissions()


class ProjectAccessDetail(generics.RetrieveDestroyAPIView):
    serializer_class = ProjectAccessDetailSerializer
    permission_classes = (IsProjectOwner,)
    queryset = ProjectAccess.objects.all()
    # TODO: be sure users see what they see


class TaskAccessList(generics.ListCreateAPIView):
    # TODO: this needs reviewing + security checks
    permission_classes = (IsAuthenticated,)
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = TaskAccessFilter

    def get_serializer_class(self):
        if self.request.method == "POST":
            return TaskAccessDetailSerializer
        else:
            return TaskAccessSerializer

    def get_queryset(self):
        # TODO: don't let people without task access to list it
        task_accesses = TaskAccess.objects.filter(
            task__id=self.request.GET.get("task")
        ).order_by("id")
        return task_accesses

    def perform_create(self, serializer):
        if self.request.user != serializer.validated_data["task"].owner:
            raise PermissionDenied()
        task_access = serializer.save()
        Log.objects.create(
            task=task_access.task,
            user=self.request.user,
            message=f"New user assigned to the task: {task_access.user}",
        )

        # TODO: fix this - /api/schema is killed here

    # def get_permissions(self):
    #     if self.request.method != "GET":
    #         project = Project.objects.filter(
    #             id=self.request.POST.get("project")
    #         ).first()
    #         if not project or project.owner != self.request.user:
    #             raise PermissionDenied()
    #
    #     return super().get_permissions()


class TaskAccessDetail(generics.RetrieveDestroyAPIView):
    # TODO: tests missing
    serializer_class = TaskAccessDetailSerializer
    permission_classes = (IsTaskOwner,)
    queryset = TaskAccess.objects.all()

    def perform_destroy(self, instance):
        Log.objects.create(
            task=instance.task,
            user=self.request.user,
            message=f"User unassigned from the task: {instance.user}",
        )
        instance.delete()

    # TODO: be sure users see what they see


class TaskPositionChangeView(APIView):
    def post(self, request, pk):
        # This might need rethinking since it requires quite a lot of updates.
        # Position is absolute within ALL projects so when the system grows each change will take more time
        # maybe it should work on 'previous/next' task logic - but that makes queries more difficult
        # what can break here is when reordering positions inside a project how will it relate to all positions

        # current solution takes task_above_id - if it's None it's going to be first ... but now what if
        # that's inside a project... should I have a separate one for within the project ... it's going to be
        # quite messy, also how this impacts if other users have other tasks - not visible to the current user

        # I already have a new model - UserTaskQueue which should sort that out per user so this is still confusing

        tasks = Task.objects.filter(is_closed=False).order_by("position")
        task = Task.objects.get(pk=pk)
        task_above_id = request.data.get("task_above_id")
        print(f"Task above id found: {task_above_id}")

        task_above = (
            Task.objects.get(pk=task_above_id) if task_above_id else None
        )

        if not task_above:
            task.position = 0
            task.save()

        position_counter = 1
        for ta in tasks:
            print(f"{ta.title} | {ta.position} | {ta.id}")

            if ta == task:
                if not task_above:
                    continue
                else:
                    ta.position = task_above.position + 1
                    print("\t Setting position to one above ")
            else:
                position_counter += 2
                ta.position = position_counter
                print(f"\t Setting position to {ta.position}")
            ta.save()

        # TODO: create log entry
        return JsonResponse({"test": task_above_id})


class TaskStartWorkView(APIView):
    def post(self, request, pk):
        # TODO: permissions check
        # TODO: add tests

        task = Task.objects.get(pk=pk)

        for tws in TaskWorkSession.objects.filter(
            user=request.user, stopped_at__isnull=True
        ):
            tws.stopped_at = now()
            tws.save()

        twa = TaskWorkSession.objects.create(
            task=task, user=request.user, started_at=now()
        )

        Log.objects.create(
            task=task,
            user=request.user,
            message=f"User {request.user} started working on this task.",
        )

        ws = WebsocketHelper()
        ws.send(
            f"USR_{request.user.id}",
            "current_task_update",
            data={"task_id": f"{task.id}"},
        )

        return JsonResponse({"id": f"{twa.id}", "status": "OK", "message": ""})


class TaskCloseView(APIView):
    def post(self, request, pk):
        # TODO: add tests

        task = Task.objects.get(pk=pk)
        if task.owner != request.user:
            raise Exception("Only task owner can close the task")

        Log.objects.create(
            task=task, user=self.request.user, message="Task closed"
        )
        if request.data.get("closing_message"):
            comment = Comment.objects.create(
                task=task,
                author=self.request.user,
                content=request.data.get("closing_message"),
            )
            create_notification_from_comment(comment)

        task.is_closed = True
        task.archived_at = now()  # TODO: think if I need this? or rename
        task.save()

        return JsonResponse({"status": "OK", "message": "Task Closed"})


class TaskUnCloseView(APIView):
    def post(self, request, pk):
        # TODO: add tests

        task = Task.objects.get(pk=pk)
        if task.owner != request.user:
            raise Exception("Only task owner can close the task")

        Log.objects.create(
            task=task, user=self.request.user, message="Task unclosed"
        )
        task.is_closed = False
        task.archived_at = None
        task.save()

        return JsonResponse({"status": "OK", "message": "Task Unclosed"})


class TaskStopWorkView(APIView):
    def post(self, request, pk):
        # TODO: permissions check, add log
        task = Task.objects.get(pk=pk)
        tws = TaskWorkSession.objects.filter(
            user=request.user, task=task, stopped_at__isnull=True
        ).first()
        if tws:
            tws.stopped_at = now()
            tws.save()

            Log.objects.create(
                task=task,
                user=request.user,
                message=f"User {request.user} stopped working on this task.",
            )

            return JsonResponse({"id": tws.id, "status": "OK", "message": ""})
        else:
            return JsonResponse(
                {
                    "id": 0,
                    "status": "ERROR",
                    "message": "This session is already stopped",
                }
            )


class CurrentTaskView(APIView):
    def get(self, request):
        user = request.user
        if request.GET.get("user"):
            user = User.objects.get(pk=request.GET.get("user"))

        task_work_session = TaskWorkSession.objects.filter(
            user=user, stopped_at__isnull=True
        ).last()

        response = {}
        if not task_work_session:
            return JsonResponse(response)

        if not user_can_see_task(user, task_work_session.task):
            return JsonResponse(response)

        if not user_can_see_task(request.user, task_work_session.task):
            return JsonResponse(response)

        serializer = TaskReadOnlySerializer(
            task_work_session.task, context={"request": request}
        )
        response = serializer.data
        return JsonResponse(response)


class UploadView(APIView):
    def post(self, request):
        # TODO: permissions check, only for users

        task_id = request.POST.get("task_id")
        project_id = request.POST.get("project_id")
        if not any([task_id, project_id]):
            return JsonResponse(
                {"error": "task_id or project_id must be sent"}
            )

        # if task_id and project_id:
        #     project_id = None

        if task_id:
            project_id = Task.objects.get(pk=task_id).project_id

        response = []

        for filename, file in request.FILES.items():
            day = now().strftime("%Y-%m-%d")
            file_extension = pathlib.Path(file.name).suffix
            slug = slugify(pathlib.Path(file.name).stem)
            short_uid = uuid.uuid4()
            storage_path = f"{day}/{short_uid}_{slug}{file_extension}"
            default_storage.save(storage_path, file)
            mt = mimetypes.guess_type(storage_path)
            if "image/" in mt[0]:
                thumbnail_path = storage_path
                # TODO: create thumbnail if it's an image, this should probably be done in celery task ...
            else:
                thumbnail_path = None

            # file_url = default_storage.url(file_name)
            # TODO: I can create some demo assets to use and put to static or cdn or sth

            att = Attachment.objects.create(
                task_id=task_id,
                project_id=project_id,
                file_path=storage_path,
                owner=request.user,
                title=slug,
                thumbnail_path=thumbnail_path,  # TODO make this thumbnail
            )

            serializer = AttachmentListSerializer(att)
            response.append(serializer.data)

        return JsonResponse({"attachments": response})


class DictionaryView(APIView):
    def get(self, request):
        return JsonResponse(
            {
                "task_status_choices": Task.StatusChoices.choices,
                "task_urgency_level_choices": Task.UrgencyLevelChoices.choices,
            },
        )


class NotificationAckListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = NotificationAckSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = NotificationAckFilter

    def get_queryset(self):
        acks = NotificationAck.objects.filter(user=self.request.user)
        return acks


class NotificationAckConfirmView(APIView):
    def post(self, request, pk):
        na = NotificationAck.objects.filter(
            pk=pk, user=self.request.user
        ).first()
        if not na:
            return JsonResponse({"status": "OK"})
        na.status = NotificationAck.Status.READ
        na.save()

        return JsonResponse({"status": "OK"})


class UserTaskQueueView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserTaskQueueSerializer

    def get_queryset(self):
        user = self.request.user
        if self.request.GET.get("user"):
            user = User.objects.get(pk=self.request.GET.get("user"))

        utq = (
            UserTaskQueue.objects.filter(user=user)
            .exclude(task__is_closed=True)
            .order_by("-priority")
        )
        return utq


class UserTaskQueueManageView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, pk):
        """Return all users that has queue for this task"""
        task = Task.objects.get(pk=pk)
        users = [u.user for u in UserTaskQueue.objects.filter(task=task)]
        serializer = UserSerializer(users, many=True)
        response = serializer.data

        return JsonResponse({"users": response})

    def post(self, request, pk):
        # TODO: test, permission check
        task = Task.objects.get(pk=pk)
        body = request.body
        user = request.user
        request_user = request.POST.get("user")

        if not request_user:
            try:
                jdata = json.loads(body)
                request_user = jdata.get("user")
            except Exception:
                pass

        if request_user:
            user = User.objects.get(pk=request_user)

        Log.objects.create(
            task=task, user=self.request.user, message="Task added to queue"
        )

        UserTaskQueue.objects.get_or_create(task=task, user=user)
        return JsonResponse({"status": "OK"})

    def delete(self, request, pk):
        # TODO: test, permission check
        task = Task.objects.get(pk=pk)
        body = request.body
        print(request.body)
        request_user = request.POST.get("user")
        user = request.user

        if not request_user:
            try:
                jdata = json.loads(body)
                request_user = jdata.get("user")
            except Exception:
                pass

        if request_user:
            user = User.objects.get(pk=request_user)

        utq = UserTaskQueue.objects.filter(task=task, user=user)
        if utq.exists():
            utq.delete()

        Log.objects.create(
            task=task,
            user=self.request.user,
            message="Task removed from queue",
        )

        return JsonResponse({"status": "OK"})


class UserTaskQueuePositionChangeView(APIView):
    def post(self, request, pk):
        # TODO: permissions + logs

        utq = UserTaskQueue.objects.get(pk=pk)
        data = json.loads(request.body)
        user_task_above_id = data.get("task_above_id")
        sorted_tasks = []

        if not user_task_above_id:
            sorted_tasks.append(utq)

        user = utq.user

        for ut in (
            UserTaskQueue.objects.filter(user=user)
            .exclude(id=utq.id)
            .order_by("-priority")
        ):
            sorted_tasks.append(ut)
            if user_task_above_id == ut.id:
                sorted_tasks.append(utq)

        counter = len(sorted_tasks)
        for st in sorted_tasks:
            counter -= 1
            st.priority = counter
            st.save()

        return JsonResponse({"status": "OK"})


class ReminderListView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ReminderSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = ReminderFilter

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ReminderReadOnlySerializer
        return ReminderSerializer

    def get_queryset(self):
        reminders = Reminder.objects.filter(user=self.request.user).exclude(
            closed_at__isnull=False
        )
        return reminders

    def perform_create(self, serializer):
        reminder = serializer.save(created_by=self.request.user)
        Log.objects.create(
            task=reminder.task,
            user=self.request.user,
            message=f"Reminder created for {self.request.user} on {reminder.reminder_date}",
        )


class ReminderCloseView(APIView):
    def post(self, request, pk):
        # TODO: permissions
        reminder = Reminder.objects.get(pk=pk)
        reminder.closed_at = now()
        reminder.save()
        Log.objects.create(
            task=reminder.task,
            user=self.request.user,
            message=f"Reminder closed for {self.request.user}",
        )
        return JsonResponse({"status": "OK"})


class ChangeTaskOwnerView(APIView):
    # This should be done by Task serializer/view but I'm having too much trouble atm for some reason
    # This should be fixed and changed

    def post(self, request, pk):
        task = Task.objects.get(pk=pk)
        if task.owner != request.user:
            if task.project and task.project.owner != request.user:
                raise Exception(
                    "Only task or project owner can change task owner"
                )

        new_owner_id = request.data.get("owner")

        new_owner = User.objects.get(pk=new_owner_id)
        task.owner = new_owner
        task.save()
        Log.objects.create(
            task=task, user=request.user, message="Owner of the task changed"
        )
        return JsonResponse({"status": "OK"})


class ChangeProjectOwnerView(APIView):
    # This should be done by Project serializer/view but I'm having too much trouble atm for some reason
    # This should be fixed and changed

    def post(self, request, pk):
        project = Project.objects.get(pk=pk)

        if project.owner != request.user:
            raise Exception("Only project owner can change project owner")

        new_owner_id = request.data.get("owner")
        new_owner = User.objects.get(pk=new_owner_id)
        project.owner = new_owner
        project.save()
        Log.objects.create(
            project=project,
            user=request.user,
            message="Owner of the project changed",
        )
        return JsonResponse({"status": "OK"})


class PinnedTaskList(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TaskListSerializer

    def get_queryset(self):
        pinned_tasks = (
            Task.objects.filter(pinned_tasks__user=self.request.user)
            .distinct()
            .order_by("urgency_level")
        )
        return pinned_tasks


class PinTaskDetail(generics.GenericAPIView):
    http_method_names = ("post", "delete")
    serializer_class = PinDetailSerializer

    def has_task_access(self, task):
        has_task_access = HasTaskAccess().has_object_permission(
            self.request, self, task
        )
        if not has_task_access:
            raise PermissionDenied()

        return True

    def get_task(self):
        task_id = self.kwargs.get("task_id", 0)
        task = Task.objects.filter(id=task_id).first()
        if not task:
            raise PermissionDenied()

        return task

    def post(self, request, task_id):
        task = self.get_task()
        self.has_task_access(task)

        if Pin.objects.filter(user=self.request.user, task=task).exists():
            return Response(status=status.HTTP_304_NOT_MODIFIED)

        serializer = self.get_serializer(
            data={"task": task.id, "user": request.user.id}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, task_id):
        task = self.get_task()
        self.has_task_access(task)
        pin = Pin.objects.filter(user=self.request.user, task=task).first()

        if not pin:
            return Response(status=status.HTTP_304_NOT_MODIFIED)

        pin.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class TestCIReloadView(APIView):
    def get(self, request):
        return JsonResponse({"value": "test-after-reload"})


class WorkSessionsBreakdownView(APIView):
    permission_classes = (IsAuthenticated,)  # TODO: Are we sure about that?

    def post(self, request):
        serializer = WorkSessionsBreakdownInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        work_sessions = TaskWorkSession.objects.filter(
            Q(started_at__date__gte=serializer.data.get("start_date"))
            & Q(stopped_at__date__lte=serializer.data.get("end_date"))
            & Q(user_id=serializer.data.get("user_id"))
        )
        s = WorkSessionsWSBSerializer(work_sessions, many=True)

        work_sessions_annotated = work_sessions.annotate(
            date=F("started_at__date"),
            task_name=F("task__title"),
        ).order_by("date")

        # Create entries maps
        sessions_by_day = defaultdict(list)  # date as key
        tasks_total = defaultdict(int)  # task name as key

        for session in work_sessions_annotated:
            date_as_key = session.started_at.strftime("%Y-%m-%d")
            sessions_by_day[date_as_key].append(session)
            tasks_total[session.task_name] += session.total_time

        # Calculate daily totals
        sessions_by_day_total = defaultdict(lambda: {"total": 0})
        for date, day_data in sessions_by_day.items():
            day_total = sum([entry.total_time for entry in day_data])
            day_total_h, day_total_m, _ = time_from_seconds(day_total)
            sessions_by_day_total[date] = f"{day_total_h:02}:{day_total_m:02}"

        # Format task totals
        for task_name, task_total in tasks_total.items():
            task_total_h, task_total_m, _ = time_from_seconds(task_total)
            tasks_total[task_name] = f"{task_total_h:02}:{task_total_m:02}"

        # Overall total across all tasks
        total_time_sum = work_sessions.aggregate(
            time_sum=Sum("total_time")
        ).get("time_sum")
        total_hours, total_minutes, _ = time_from_seconds(total_time_sum)
        total_time_sum_str = f"{total_hours:02}:{total_minutes:02}"

        return Response(
            data={
                "events": s.data,
                "total_sum": total_time_sum_str,
                "sessions_by_day": sessions_by_day_total,
                "tasks_total": tasks_total,
            },
            status=status.HTTP_200_OK,
        )
