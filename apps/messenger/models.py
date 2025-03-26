import uuid

from django.db import models

from core.models import User

class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Thread(BaseModel):
    task_id = models.UUIDField(null=True, blank=True)
    project_id = models.UUIDField(null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(task_id__isnull=True, project_id__isnull=False)
                | models.Q(task_id__isnull=False, project_id__isnull=True),
                name="thread_must_have_either_task_or_project",
            )
        ]
        ordering = ['-created_at']


class Message(BaseModel):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()

    class Meta:
        ordering = ['-created_at']


class MessageAck(BaseModel):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="acks")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    seen_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("message", "user")
        ordering = ['-created_at']


class DirectThread(BaseModel):
    users = models.ManyToManyField(User, related_name="threads")

    class Meta:
        ordering = ['-created_at']


class DirectMessage(BaseModel):
    thread = models.ForeignKey("DirectThread", on_delete=models.CASCADE, related_name="direct_messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()

    class Meta:
        ordering = ['-created_at']


class DirectMessageAck(BaseModel):
    message = models.ForeignKey(DirectMessage, on_delete=models.CASCADE, related_name="acks")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    seen_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("message", "user")
        ordering = ['-created_at']
