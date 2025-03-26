from core.models import ProjectAccess, TaskAccess


def user_can_see_task(user, task):
    if task.owner == user:
        return True

    if task.project and task.project.owner == user:
        return True

    if TaskAccess.objects.filter(user=user, task=task).exists():
        return True

    if task.project:
        if ProjectAccess.objects.filter(user=user, project=task.project).exists():
            return True

    return False


def user_can_see_project(user, project):
    if project.owner == user:
        return True

    if ProjectAccess.objects.filter(project=project, user=user).exists():
        return True

    return False
