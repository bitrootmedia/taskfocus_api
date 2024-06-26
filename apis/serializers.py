from django.db.models import Sum
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
        )


class TaskReadOnlySerializer(serializers.ModelSerializer):
    owner = UserSerializer()
    responsible = UserSerializer()
    project = ProjectDetailReadOnlySerializer()
    title = serializers.SerializerMethodField()

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
            "blocks",
            "project",
            "position",
            "responsible",
            "owner",
            "is_closed",
            "urgency_level",
            "position",
            "estimated_work_hours",
            "is_urgent",
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


class TaskDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = (
            "id",
            "title",
            "description",
            "blocks",
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
