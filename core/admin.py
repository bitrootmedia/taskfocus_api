from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import Group
from simple_history.admin import SimpleHistoryAdmin

from .models import (
    Attachment,
    Beacon,
    Board,
    BoardUser,
    Card,
    CardItem,
    Comment,
    Log,
    Note,
    Notification,
    NotificationAck,
    Pin,
    Project,
    ProjectAccess,
    Reminder,
    Task,
    TaskAccess,
    TaskBlock,
    TaskChecklistItem,
    TaskWorkSession,
    Team,
    User,
    UserTaskQueue,
)

admin.site.site_header = "AyeAyeCaptain API"
admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    model = User
    fieldsets = (  # type: ignore
        *DjangoUserAdmin.fieldsets,
        (
            "Custom fields",
            {"fields": ("config", "teams", "pushover_user", "notifier_user")},
        ),
    )


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "task",
        "project",
        "owner",
        "created_at",
        "is_deleted",
        "archived_at",
    )
    list_filter = (
        "title",
        "task",
        "project",
        "owner",
        "created_at",
        "is_deleted",
        "archived_at",
    )


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        "task",
        "project",
        "author",
        "response_to_comment",
        "created_at",
        "archived_at",
    )
    list_filter = (
        "task",
        "project",
        "author",
        "response_to_comment",
        "created_at",
        "archived_at",
    )

    search_fields = ("content",)


@admin.register(Log)
class LogAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "task",
        "project",
        "comment",
        "action",
        "created_at",
        "archived_at",
    )
    list_filter = (
        "user",
        "task",
        "project",
        "comment",
        "action",
        "created_at",
        "archived_at",
    )


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "owner",
        "last_updated",
        "created_at",
    )
    list_filter = (
        "title",
        "owner",
        "last_updated",
        "created_at",
    )


@admin.register(ProjectAccess)
class ProjectAccessAdmin(admin.ModelAdmin):
    list_display = (
        "project",
        "user",
    )
    list_filter = (
        "project",
        "user",
    )


class TaskAccessInline(admin.TabularInline):
    model = TaskAccess
    extra = 1


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "project",
        "tag",
        "parent_task",
        "owner",
        "is_closed",
        "progress",
        "eta_date",
        "responsible",
        "status",
        "created_at",
    )
    list_filter = (
        "project",
        "tag",
        "owner",
        "is_closed",
        "responsible",
        "status",
    )

    inlines = [TaskAccessInline]
    search_fields = ("title",)


@admin.register(TaskBlock)
class TaskBlockAdmin(SimpleHistoryAdmin):
    list_display = (
        "task",
        "block_type",
        "position",
        "created_at",
        "updated_at",
        "created_by",
    )
    list_filter = ("task", "block_type", "created_by")


@admin.register(TaskAccess)
class TaskAccessAdmin(admin.ModelAdmin):
    list_display = (
        "task",
        "user",
    )
    list_filter = (
        "task",
        "user",
    )


@admin.register(TaskWorkSession)
class TaskWorkSessionAdmin(admin.ModelAdmin):
    list_display = (
        "task",
        "user",
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("created_at",)


@admin.register(NotificationAck)
class NotificationAckAdmin(admin.ModelAdmin):
    list_display = ("created_at",)


@admin.register(UserTaskQueue)
class UserTaskQueueAdmin(admin.ModelAdmin):
    list_display = ("id",)


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ("id",)


@admin.register(TaskChecklistItem)
class TaskChecklistItemAdmin(admin.ModelAdmin):
    list_display = ("id",)


class UserInline(admin.TabularInline):
    model = User.teams.through


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name",)
    inlines = [UserInline]


@admin.register(Pin)
class PinAdmin(admin.ModelAdmin):
    list_display = ("user", "task", "project")


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ("user", "title", "created_at", "updated_at")


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ("name", "owner")


@admin.register(BoardUser)
class BoardUserAdmin(admin.ModelAdmin):
    list_display = ("board", "user")


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ("board", "name")


@admin.register(CardItem)
class CardItemAdmin(admin.ModelAdmin):
    list_display = ("task", "card")


@admin.register(Beacon)
class BeaconAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at", "confirmed_at")
