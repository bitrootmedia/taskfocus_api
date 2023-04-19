import uuid
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    image = models.ImageField(upload_to="user_avatar", blank=True)
    archived_at = models.DateTimeField(null=True, blank=True)


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
        TODO = "TODO", "TODO"
        IN_PROGRESS = "IN PROGRESS", "IN PROGRESS"
        BLOCKER = "BLOCKER", "BLOCKER"
        TO_VERIFY = "TO VERIFY", "TO VERIFY"
        DONE = "DONE", "DONE"
        ON_HOLD = "ON_HOLD", "ON_HOLD"

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
    position = models.IntegerField(null=True, blank=True)
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
    progress = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)], default=0
    )
    eta_date = models.DateField(null=True, blank=True)
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
    file_path = models.FileField(upload_to="attachments")
    thumbnail_path = models.ImageField(
        upload_to="attachment_thumbnails", blank=True
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
