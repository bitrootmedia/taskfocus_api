from django.db.models import Sum, Q
from rest_framework import serializers

from core.models import (
    Project,
    Task,
    Log,
    Comment,
    Attachment,
    ProjectAccess,
    TaskAccess,
    TaskWorkSession,
    User,
    Notification,
    NotificationAck,
    UserTaskQueue,
    Reminder,
    TaskChecklistItem,
    PrivateNote,
    TaskBlock,
    Pin,
    Note,
    Board,
    Card,
    CardItem,
    BoardUser,
)
from core.utils.permissions import user_can_see_task, user_can_see_project
from core.utils.time_from_seconds import time_from_seconds

masked_string = "*" * 5


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "first_name", "last_name", "config")


class ProjectListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ("id", "title", "progress", "tag", "is_closed")


class ProjectListReadOnlySerializer(serializers.ModelSerializer):
    owner = UserSerializer()
    title = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ("id", "title", "owner", "progress", "tag", "is_closed")

    def get_title(self, instance):
        request = self.context.get("request")
        if request:
            user = request.user
            if user_can_see_project(user, instance):
                return instance.title
            else:
                return masked_string
        else:
            return instance.title


class ProjectDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = (
            "id",
            "title",
            "description",
            "background_image",
            "progress",
            "tag",
            "is_closed",
        )


class ProjectDetailReadOnlySerializer(serializers.ModelSerializer):
    owner = UserSerializer()
    title = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = (
            "id",
            "title",
            "description",
            "background_image",
            "owner",
            "progress",
            "tag",
            "is_closed",
        )

    def get_title(self, instance):
        request = self.context.get("request")
        if request:
            user = request.user
            if user_can_see_project(user, instance):
                return instance.title
            else:
                return masked_string
        else:
            return instance.title


class TaskListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = (
            "id",
            "title",
            "status",
            "eta_date",
            "created_at",
            "updated_at",
            "tag",
            "progress",
            "description",
            "project",
            "position",
            "responsible",
            "urgency_level",
            "position",
            "estimated_work_hours",
            "is_urgent",
            "follow_up",
        )


class TaskReadOnlySerializer(serializers.ModelSerializer):
    owner = UserSerializer()
    responsible = UserSerializer()
    project = ProjectDetailReadOnlySerializer()
    title = serializers.SerializerMethodField()
    is_pinned = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = (
            "id",
            "title",
            "status",
            "eta_date",
            "created_at",
            "updated_at",
            "tag",
            "progress",
            "description",
            "project",
            "position",
            "responsible",
            "owner",
            "is_closed",
            "urgency_level",
            "position",
            "estimated_work_hours",
            "is_urgent",
            "follow_up",
            "is_pinned",
        )

    def get_title(self, instance):
        request = self.context.get("request")
        if request:
            user = request.user
            if user_can_see_task(user, instance):
                return instance.title
            else:
                return masked_string
        else:
            return instance.title

    def get_is_pinned(self, instance):
        request = self.context.get("request")
        user = getattr(request, "user", None)

        if request and user and instance:
            return Pin.objects.filter(Q(user=user) & Q(task=instance)).exists()

        return False


class TaskDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = (
            "id",
            "title",
            "description",
            "tag",
            "position",
            "progress",
            "eta_date",
            "status",
            "project",
            "responsible",
            "urgency_level",
            "position",
            "estimated_work_hours",
            "is_urgent",
            "follow_up",
            # "owner",
            "created_at",
            "updated_at",
        )


class TaskTotalTimeReadOnlySerializer(serializers.ModelSerializer):
    total_time = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = ("id", "total_time")

    def get_total_time(self, instance: Task):
        total_seconds = instance.task_work.aggregate(
            time_sum=Sum("total_time")
        ).get("time_sum", 0)
        if not total_seconds:
            total_seconds = 0
        hours, minutes, _ = time_from_seconds(total_seconds)
        return {"hours": f"{hours:02}", "minutes": f"{minutes:02}"}


class TaskBlockListSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskBlock
        fields = (
            "id",
            "block_type",
            "position",
            "content",
            "created_at",
            "updated_at",
            "created_by",
        )
        read_only_fields = ("created_by",)


class TaskBlockDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskBlock
        fields = (
            "id",
            "position",
            "content",
        )


class LogListSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    task = TaskReadOnlySerializer()
    project = ProjectDetailSerializer()

    class Meta:
        model = Log
        fields = ("id", "message", "created_at", "user", "task", "project")


class CommentListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ("id", "content", "task", "project")


class CommentListReadOnlySerializer(serializers.ModelSerializer):
    author = UserSerializer()
    task = TaskReadOnlySerializer()
    project = ProjectDetailSerializer()

    class Meta:
        model = Comment
        fields = ("id", "content", "task", "project", "author", "created_at")


class CommentDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ("id", "content", "task_id", "project_id")


class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ("id", "title", "content", "tag", "created_at", "updated_at")
        read_only_fields = ("title",)

    def get_title_from_content(self):
        """Get first 50 chars of content to use as a title"""
        content = self.validated_data.get("content", "")
        title = content.split("\n")[0][:50]
        return title


class PrivateNoteListSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrivateNote
        fields = ("id", "note", "task", "created_at", "updated_at")


class PrivateNoteDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrivateNote
        fields = ("id", "note", "task_id")


class TaskSessionDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskWorkSession
        fields = (
            "id",
            "started_at",
            "stopped_at",
            "total_time",
            "user",
            "message",
            "task",
        )


class TaskSessionListSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    task = TaskReadOnlySerializer()

    class Meta:
        model = TaskWorkSession
        fields = (
            "id",
            "started_at",
            "stopped_at",
            "total_time",
            "user",
            "message",
            "task",
        )


class AttachmentListSerializer(serializers.ModelSerializer):
    owner = UserSerializer()
    task = TaskReadOnlySerializer()
    project = ProjectDetailSerializer()

    class Meta:
        model = Attachment
        fields = (
            "id",
            "title",
            "file_path",
            "thumbnail_path",
            "created_at",
            "owner",
            "task",
            "project",
        )


class AttachmentDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = ("id", "title")


class ProjectAccessSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = ProjectAccess
        fields = ("id", "project", "user")


class ProjectAccessDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectAccess
        fields = ("id", "project", "user")


class TaskAccessSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = TaskAccess
        fields = ("id", "task", "user")


class TaskAccessDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskAccess
        fields = ("id", "task", "user")


class NotificationSerializer(serializers.ModelSerializer):
    project = ProjectDetailSerializer()
    task = TaskDetailSerializer()
    comment = CommentDetailSerializer()

    class Meta:
        model = Notification
        fields = ("tag", "content", "project", "task", "comment")


class NotificationAckSerializer(serializers.ModelSerializer):
    notification = NotificationSerializer()
    user = UserSerializer()

    class Meta:
        model = NotificationAck
        fields = ("id", "notification", "created_at", "status", "user")


class UserTaskQueueSerializer(serializers.ModelSerializer):
    task = TaskReadOnlySerializer()

    class Meta:
        model = UserTaskQueue
        fields = ("id", "priority", "task")


class TaskChecklistItemSerializer(serializers.ModelSerializer):
    task = TaskReadOnlySerializer()

    class Meta:
        model = TaskChecklistItem
        fields = ("id", "task")


class ReminderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reminder
        fields = (
            "id",
            "user",
            "task",
            "created_by",
            "reminder_date",
            "message",
            "closed_at",
        )
        read_only_fields = ("created_by",)


class ReminderReadOnlySerializer(serializers.ModelSerializer):
    task = TaskReadOnlySerializer()

    class Meta:
        model = Reminder
        fields = (
            "id",
            "user",
            "task",
            "created_by",
            "reminder_date",
            "message",
            "closed_at",
        )
        read_only_fields = ("created_by",)


class PinDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pin
        fields = (
            "id",
            "user",
            "task",
            "project",
        )


class WorkSessionsBreakdownInputSerializer(serializers.Serializer):
    user_id = serializers.UUIDField(required=True)
    timezone = ...  # TODO: Details for that
    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=True)


class WorkSessionsWSBSerializer(serializers.ModelSerializer):
    start = serializers.DateTimeField(
        format="%Y-%m-%d %H:%M", source="started_at"
    )
    end = serializers.DateTimeField(
        format="%Y-%m-%d %H:%M", source="stopped_at"
    )
    title = serializers.CharField(source="task.title")
    task_id = serializers.UUIDField(source="task.id")

    class Meta:
        model = TaskWorkSession
        fields = ("start", "end", "title", "task_id", "total_time")


class BoardSerializer(serializers.ModelSerializer):
    """Used to edit only board specific fields (not cards or card items)"""

    class Meta:
        model = Board
        fields = ("id", "name", "owner", "config")


class BoardUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = BoardUser
        fields = ("id", "board", "user")


class CardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Card
        fields = ("id", "board", "name", "position", "config")


class CardItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CardItem
        fields = (
            "id",
            "task",
            "project",
            "board",
            "comment",
            "card",
            "position",
            "config",
        )


class CardItemReadOnlySerializer(serializers.ModelSerializer):
    task = TaskReadOnlySerializer()
    project = ProjectDetailReadOnlySerializer()
    board = BoardSerializer()

    class Meta:
        model = CardItem
        fields = (
            "id",
            "task",
            "project",
            "board",
            "comment",
            "card",
            "position",
            "config",
        )


class CardReadOnlySerializer(serializers.ModelSerializer):
    card_items = CardItemReadOnlySerializer(many=True)

    class Meta:
        model = Card
        fields = ("id", "board", "name", "position", "card_items", "config")


class BoardReadonlySerializer(serializers.ModelSerializer):
    cards = CardReadOnlySerializer(many=True)
    is_pinned = serializers.SerializerMethodField()

    class Meta:
        model = Board
        fields = ("id", "name", "owner", "cards", "config", "is_pinned")

    def get_is_pinned(self, instance):
        request = self.context.get("request")
        user = getattr(request, "user", None)

        if request and user and instance:
            return Pin.objects.filter(
                Q(user=user) & Q(board=instance)
            ).exists()

        return False
