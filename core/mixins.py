from rest_framework.exceptions import PermissionDenied

from apis.permissions import HasTaskAccess
from core.models import Task


class TaskAccessMixin:
    """
    Expose `get_task` method used to check if `request.user` has access to given task based on task id.
    Return Task instance if True or raise PermissionDenied otherwise.
    """

    def get_task(self, task_id=0):
        task = Task.objects.filter(id=task_id).first()
        if not task:
            raise PermissionDenied(f"Task not found for id: {task_id}")
        has_task_access = HasTaskAccess().has_object_permission(
            getattr(self, "request", {}), self, task
        )
        if not has_task_access:
            raise PermissionDenied(
                f"Not allowed to access the task (id: {task_id})"
            )
        return task
