from core.models import User, TaskAccess, ProjectAccess, Notification, NotificationAck


def extract_users_from_text(text):
    """Used to extract unique usernames from text"""
    all_users = User.objects.all()

    users_found = set()
    for u in all_users:
        if f'@{u.username} '.casefold() in text.casefold():
            users_found.add(u)

    return users_found


def create_notification_from_comment(comment):
    if not comment.content:
        return

    notify_users = set()

    if '@task ' in comment.content:
        if comment.task:
            for ta in TaskAccess.objects.filter(task=comment.task):
                notify_users.add(ta.user)
            if comment.task.owner:
                notify_users.add(comment.task.owner)

    project = None
    if '@project ' in comment.content:
        if comment.project:
            project = comment.project
        if not project and comment.task and comment.task.project:
            project = comment.task.project

        if project:
            for ta in ProjectAccess.objects.filter(project=project):
                notify_users.add(ta.user)
            if project.owner:
                notify_users.add(project.owner)

    mentioned_users = extract_users_from_text(comment.content)

    notify_users = notify_users | mentioned_users

    if not notify_users:
        return

    snippet = comment.content[:100]
    notification = Notification.objects.create(
        comment=comment,
        task=comment.task,
        project=project,
        content=f"New comment: {snippet}"
    )

    for nu in notify_users:
        if nu == comment.author:
            continue

        NotificationAck.objects.create(
            user=nu,
            notification=notification
        )
