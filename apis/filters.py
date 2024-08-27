import django_filters
from django.db.models import Q
from django_filters import rest_framework as filters
from core.models import (
    Project,
    Task,
    Log,
    Comment,
    Attachment,
    ProjectAccess,
    TaskAccess,
    Reminder,
    NotificationAck,
    TaskWorkSession,
    PrivateNote,
)


class ProjectFilter(filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr="icontains")
    show_closed = django_filters.BooleanFilter(field_name="is_closed")

    class Meta:
        model = Project
        fields = ["title", "show_closed"]


class TaskFilter(filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr="icontains")
    project__title = django_filters.CharFilter(lookup_expr="icontains")
    created_at = filters.DateFromToRangeFilter()
    query = filters.CharFilter(method="filter_by_all_fields")

    class Meta:
        model = Task
        fields = [
            "title",
            "project",
            "project__title",
            "is_closed",
            "is_urgent",
            "responsible",
            "status",
            "owner",
            "created_at",
            "updated_at",
            "tag",
            "query",
            "urgency_level",
        ]

    def filter_by_all_fields(self, queryset, name, value):
        return queryset.filter(
            Q(title__icontains=value)
            | Q(description__icontains=value)
            | Q(tag__icontains=value)
            # | Q(blocks__icontains=value)
        )


class ReminderFilter(filters.FilterSet):
    open_only = django_filters.BooleanFilter(
        field_name="closed_at", lookup_expr="isnull"
    )

    class Meta:
        model = Reminder
        fields = ["task", "user", "closed_at"]


class NotificationAckFilter(filters.FilterSet):
    class Meta:
        model = NotificationAck
        fields = ["status", "id"]


class LogFilter(filters.FilterSet):
    message = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Log
        fields = ["message", "project", "task"]


class CommentFilter(filters.FilterSet):
    class Meta:
        model = Comment
        fields = ["project", "content", "task"]


class PrivateNoteFilter(filters.FilterSet):
    class Meta:
        model = PrivateNote
        fields = ["user", "task"]


class AttachmentFilter(filters.FilterSet):
    class Meta:
        model = Attachment
        fields = ["project", "task"]


class TaskSessionFilter(filters.FilterSet):
    class Meta:
        model = TaskWorkSession
        fields = ["task", "user"]


class ProjectAccessFilter(filters.FilterSet):
    class Meta:
        model = ProjectAccess
        fields = ["id", "project"]


class TaskAccessFilter(filters.FilterSet):
    class Meta:
        model = TaskAccess
        fields = ["id", "task"]
