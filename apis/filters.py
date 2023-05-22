import django_filters
from django_filters import rest_framework as filters
from core.models import (
    Project,
    Task,
    Log,
    Comment,
    Attachment,
    ProjectAccess,
    TaskAccess, Reminder,
)


class ProjectFilter(filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Project
        fields = [
            "title",
        ]


class TaskFilter(filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Task
        fields = ["title", "project", "is_closed"]


class ReminderFilter(filters.FilterSet):

    class Meta:
        model = Reminder
        fields = ["task"]



class LogFilter(filters.FilterSet):
    message = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Log
        fields = ["message", "project", "task"]


class CommentFilter(filters.FilterSet):
    class Meta:
        model = Comment
        fields = ["project", "content", "task"]


class AttachmentFilter(filters.FilterSet):
    class Meta:
        model = Attachment
        fields = ["project", "task"]


class ProjectAccessFilter(filters.FilterSet):
    class Meta:
        model = ProjectAccess
        fields = ["id", "project"]


class TaskAccessFilter(filters.FilterSet):
    class Meta:
        model = TaskAccess
        fields = ["id", "task"]
