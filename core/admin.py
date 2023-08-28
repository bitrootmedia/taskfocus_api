from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

from .models import (
    Attachment,
    Comment,
    Log,
    Project,
    ProjectAccess,
    Task,
    TaskAccess,
    User,
    TaskWorkSession,
    Notification,
    NotificationAck,
    UserTaskQueue,
    Reminder,
    TaskChecklistItem,
    Team,
)

admin.site.site_header = "Project management API"
# admin.site.register(User, UserAdmin)
admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(UserAdmin):
    model = User
    fieldsets = (
        *UserAdmin.fieldsets,
        ("Custom fields", {"fields": ("config", "teams", "pushover_user")}),
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
        "archived_at",
    )
    list_filter = (
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
        "archived_at",
    )


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
