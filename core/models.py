import uuid
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Team(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150, unique=True)

    def __str__(self):
        return f"{self.name}"


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    image = models.ImageField(upload_to="user_avatar", blank=True)
    archived_at = models.DateTimeField(null=True, blank=True)
    config = models.JSONField(default=dict, blank=True)
    teams = models.ManyToManyField(Team)


class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True)
    background_image = models.ImageField(
        upload_to="project_background", blank=True
    )
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="owned_projects"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    archived_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title


class ProjectAccess(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="permissions"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="projects",
        null=True,
        blank=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["project", "user"],
                name="core_project_access_unique_project_user",
            )
        ]

        verbose_name_plural = "Project Accesses"

    def __str__(self):
        if self.user is not None:
            return f"{self.project.title} {self.user.username}"

    def clean(self):
        if self.user is None:
            raise ValidationError("User field is required")


class Task(models.Model):
    class StatusChoices(models.TextChoices):
        OPEN = "OPEN", "OPEN"
        IN_PROGRESS = "IN PROGRESS", "IN PROGRESS"
        BLOCKER = "BLOCKER", "BLOCKER"
        TO_VERIFY = "TO VERIFY", "TO VERIFY"
        DONE = "DONE", "DONE"

    class UrgencyLevelChoices(models.TextChoices):
        CRITICAL = "CRITICAL", "CRITICAL"
        MAJOR = "MAJOR", "MAJOR"
        MEDIUM = "MEDIUM", "MEDIUM"
        MINOR = "MINOR", "MINOR"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="tasks",
        null=True,
        blank=True,
    )
    tag = models.CharField(max_length=150, blank=True)
    position = models.IntegerField(default=100, null=True, blank=True)
    parent_task = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="sub_tasks",
        null=True,
        blank=True,
    )
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="owned_tasks"
    )
    is_closed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    progress = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)], default=0
    )
    eta_date = models.DateField(null=True, blank=True)
    estimated_work_hours = models.DecimalField(null=True, blank=True, max_digits=4, decimal_places=1)
    is_urgent = models.BooleanField(default=False)
    responsible = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="managed_tasks",
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=150, blank=True, null=True, choices=StatusChoices.choices
    )
    urgency_level = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        choices=UrgencyLevelChoices.choices,
    )
    archived_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title


class TaskAccess(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(
        Task, on_delete=models.CASCADE, related_name="permissions"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="tasks",
        null=True,
        blank=True,
    )

    class Meta:

        constraints = [
            models.UniqueConstraint(
                fields=["task", "user"],
                name="core_task_access_unique_task_user",
            )
        ]

        verbose_name_plural = "Task Accesses"

    def __str__(self):
        if self.user is not None:
            return f"{self.task.title} {self.user.username}"

    def clean(self):
        if self.user is None:
            raise ValidationError("User field needs to have a value.")


class Attachment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=150)
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="attachments",
        null=True,
        blank=True,
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="attachments",
        null=True,
        blank=True,
    )
    file_path = models.FileField(upload_to="attachments", max_length=4000)
    thumbnail_path = models.ImageField(
        upload_to="attachment_thumbnails", blank=True, max_length=4000
    )
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="owned_attachments"
    )
    is_deleted = models.BooleanField(
        default=False
    )  # do I need this field (is_deleted) if I have archived_at?
    created_at = models.DateTimeField(auto_now_add=True)
    archived_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title

    def clean(self):
        if self.task is None and self.project is None:
            raise ValidationError(
                "Task field or Project field needs to have a value."
            )
        # if self.task is not None and self.project is not None:
        #     raise ValidationError(
        #         "Only Task field or Project field can have a value."
        #     )


class Comment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="comments",
        null=True,
        blank=True,
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="comments",
        null=True,
        blank=True,
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="comments"
    )
    content = models.TextField()
    response_to_comment = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="responses",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    archived_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        if self.task is not None:
            return f"{self.task.title} {self.author.username}"
        if self.project is not None:
            return f"{self.project.title} {self.author.username}"

        return f"{self.id}"

    def clean(self):
        if self.task is None and self.project is None:
            raise ValidationError(
                "Task field or Project field needs to have a value."
            )
        if self.task is not None and self.project is not None:
            raise ValidationError(
                "Only Task field or Project field can have a value."
            )


class Log(models.Model):
    class ActionType(models.TextChoices):
        CREATED = "CREATED", "Created"
        EDITED = "EDITED", "Edited"
        DELETED = "DELETED", "Deleted"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="logs"
    )
    message = models.TextField()
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="logs",
        null=True,
        blank=True,
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="logs",
        null=True,
        blank=True,
    )
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name="logs",
        null=True,
        blank=True,
    )
    action = models.CharField(max_length=7, choices=ActionType.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    archived_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]


class TaskWorkSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    started_at = models.DateTimeField(auto_now_add=True)
    stopped_at = models.DateTimeField(null=True, blank=True)

    total_time = models.IntegerField(default=0)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="task_work"
    )
    message = models.TextField(null=True, blank=True)
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="task_work",
        null=True,
        blank=True,
    )


class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    content = models.TextField(null=True, blank=True)
    tag = models.CharField(max_length=1000, null=True, blank=True)

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="task_notifications",
        null=True,
        blank=True,
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="project_notifications",
        null=True,
        blank=True,
    )
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name="comment_notifications",
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.content[:50]}"


class NotificationAck(models.Model):
    class Status(models.TextChoices):
        ARCHIVED = "ARCHIVED", "Archived"
        READ = "READ"
        UNREAD = "UNREAD"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
    )
    status = models.CharField(
        max_length=11,
        choices=Status.choices,
        default=Status.UNREAD,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]


class UserTaskQueue(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
    )
    priority = models.IntegerField(default=100, help_text="Higher is more important")

    class Meta:
        ordering = ["-priority"]


class Reminder(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reminders_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    updated_at = models.DateTimeField(auto_now=True)
    reminder_date = models.DateTimeField()
    message = models.CharField(max_length=1000, null=True, blank=True)


class TaskChecklistItem(models.Model):
    """Checklist item"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
    )
    label = models.CharField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    done_at = models.DateTimeField(null=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    position = models.IntegerField(default=0)
    done_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="checklistitem_done"
    )


class TaskUserNote(models.Model):
    """Private notes per task"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
