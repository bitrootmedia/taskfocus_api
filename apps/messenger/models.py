import uuid

from django.db import models

from core.models import Project, Task, User


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Thread(BaseModel):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, null=True, blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(task__isnull=True, project__isnull=False)
                    | models.Q(task__isnull=False, project__isnull=True)
                ),
                name="thread_must_have_either_task_or_project",
            )
        ]
        ordering = ["-created_at"]


class Message(BaseModel):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]


class ThreadAck(BaseModel):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    seen_at = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]


class DirectThread(BaseModel):
    users = models.ManyToManyField(User, related_name="threads")

    class Meta:
        ordering = ["-created_at"]


class DirectMessage(BaseModel):
    thread = models.ForeignKey("DirectThread", on_delete=models.CASCADE, related_name="direct_messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["thread", "sender", "created_at"], name="idx_thread_sender_created_at"),
        ]


class DirectThreadAck(BaseModel):
    thread = models.ForeignKey(DirectThread, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    seen_at = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["thread", "user", "-created_at"], name="idx_thread_user_created_at")]
