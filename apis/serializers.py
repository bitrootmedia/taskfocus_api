from rest_framework import serializers

from core.models import (
    Project,
    Task,
    Log,
    Comment,
    Attachment,
    ProjectAccess,
    TaskAccess,
    User, Notification, NotificationAck, UserTaskQueue,
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "first_name", "last_name")


class ProjectListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = (
            "id",
            "title",
        )


class ProjectListReadOnlySerializer(serializers.ModelSerializer):
    owner = UserSerializer()

    class Meta:
        model = Project
        fields = ("id", "title", "owner")


class ProjectDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ("id", "title", "description", "background_image")


class ProjectDetailReadOnlySerializer(serializers.ModelSerializer):
    owner = UserSerializer()

    class Meta:
        model = Project
        fields = ("id", "title", "description", "background_image", "owner")


class TaskListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = (
            "id",
            "title",
            "status",
            "eta_date",
            "created_at",
            "tag",
            "progress",
            "description",
            "project",
            "position",
            "responsible",
            "urgency_level",
        )


class TaskReadOnlySerializer(serializers.ModelSerializer):
    owner = UserSerializer()
    responsible = UserSerializer()
    project = ProjectDetailReadOnlySerializer()

    class Meta:
        model = Task
        fields = (
            "id",
            "title",
            "status",
            "eta_date",
            "created_at",
            "tag",
            "progress",
            "description",
            "project",
            "position",
            "responsible",
            "owner",
            "is_closed",
            "urgency_level",
        )


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
            # "owner",
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

    class Meta:
        model = NotificationAck
        fields = ("id", "notification", "created_at")


class UserTaskQueueSerializer(serializers.ModelSerializer):
    task = TaskReadOnlySerializer()

    class Meta:
        model = UserTaskQueue
        fields = ("id", "priority", "task")
