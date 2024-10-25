import logging
import uuid

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.timezone import now
from simple_history.models import HistoricalRecords

from core.utils.notify import notify_user
from core.utils.websockets import WebsocketHelper

logger = logging.getLogger(__name__)


class Team(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150, unique=True)

    def __str__(self):
        return f"{self.name}"


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    image = models.ImageField(upload_to="user_avatar", blank=True)
    pushover_user = models.CharField(max_length=100, null=True, blank=True)
    notifier_user = models.CharField(max_length=100, null=True, blank=True)
    archived_at = models.DateTimeField(null=True, blank=True)
    config = models.JSONField(default=dict, blank=True)
    teams = models.ManyToManyField(Team)

    class Meta:
        ordering = ["username"]


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
    progress = models.IntegerField(default=0)
    is_closed = models.BooleanField(default=False)
    tag = models.CharField(max_length=100, null=True, blank=True)

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
        ON_HOLD = "ON HOLD", "ON HOLD"
        IDEA = "IDEA", "IDEA"

    class UrgencyLevelChoices(models.TextChoices):
        TODAY = "TODAY", "TODAY"
        TOMORROW = "TOMORROW", "TOMORROW"
        IN_3_DAYS = "IN 3 DAYS", "IN 3 DAYS"
        WEEK_PLUS = "WEEK_PLUS", "WEEK PLUS"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    blocks_old = models.JSONField(default=list)
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
    estimated_work_hours = models.DecimalField(
        null=True, blank=True, max_digits=4, decimal_places=1
    )
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
    follow_up = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title


class TaskBlock(models.Model):
    class BlockTypeChoices(models.TextChoices):
        MARKDOWN = "MARKDOWN", "Markdown"
        IMAGE = "IMAGE", "Image"
        CHECKLIST = "CHECKLIST", "Checklist"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(
        Task, on_delete=models.CASCADE, related_name="blocks"
    )
    block_type = models.CharField(
        max_length=150, choices=BlockTypeChoices.choices
    )
    position = models.PositiveSmallIntegerField(default=0)
    content = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    history = HistoricalRecords()


class Pin(models.Model):
    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="pinned_tasks",
        null=True,
        blank=True,
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="pinned_projects",
        null=True,
        blank=True,
    )


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

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.task:
            ws = WebsocketHelper()
            data = {
                "id": f"{self.id}",
                "content": self.content,
                "task_id": f"{self.task.id}" if self.task else None,
                "project_id": f"{self.project.id}" if self.project else None,
            }
            ws.send(
                channel=f"{self.task.id}",
                event_name="comment_created",
                data=data,
            )


class Note(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    title = models.CharField(max_length=150)
    content = models.TextField()
    tag = models.CharField(max_length=150, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class PrivateNote(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="private_notes",
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="private_notes"
    )
    note = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


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

    started_at = models.DateTimeField(null=True, blank=True)
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

    def save(self, *args, **kwargs):
        if not self.started_at:
            self.started_at = now()

        if self.stopped_at and self.stopped_at < self.started_at:
            raise Exception("Stopped at cannot be before started at")

        if self.stopped_at and self.started_at:
            self.total_time = (
                self.stopped_at - self.started_at
            ).total_seconds()

        super().save(*args, **kwargs)


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

    def save(self, *args, **kwargs):
        if not self.created_at:
            try:
                notify_user(self.user, self.notification)
            except Exception as ex:
                logger.exception(f"{ex}")

        super().save(*args, **kwargs)


class UserTaskQueue(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
    )
    priority = models.IntegerField(
        default=100, help_text="Higher is more important"
    )

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
        User, on_delete=models.CASCADE, related_name="reminders_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    updated_at = models.DateTimeField(auto_now=True)
    reminder_date = models.DateTimeField()
    message = models.CharField(max_length=1000, null=True, blank=True)

    class Meta:
        ordering = ["reminder_date"]


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
        User, on_delete=models.CASCADE, related_name="checklistitem_done"
    )


class Board(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="owned_boards"
    )

    def user_has_board_access(self, user):
        return (self.owner == user) or self.board_users.filter(
            id=user.id
        ).exists()


class BoardUser(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    board = models.ForeignKey(
        Board, on_delete=models.CASCADE, related_name="board_users"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="board_users",  # Name is icky
    )


class Card(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    board = models.ForeignKey(
        Board, on_delete=models.CASCADE, related_name="cards"
    )
    name = models.CharField(max_length=150)
    position = models.IntegerField(default=0)


class CardTask(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(
        Task, on_delete=models.CASCADE, related_name="card_tasks"
    )
    card = models.ForeignKey(
        Card, on_delete=models.CASCADE, related_name="card_tasks"
    )
    position = models.IntegerField(default=0)
