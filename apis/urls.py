from django.urls import path
from . import views

urlpatterns = [
    path("users", views.UserList.as_view(), name="user_list"),
    path("user/<pk>", views.UserDetail.as_view(), name="user_detail"),
    path("projects", views.ProjectList.as_view(), name="project_list"),
    path("project/<pk>", views.ProjectDetail.as_view(), name="project_detail"),
    path(
        "project-accesses",
        views.ProjectAccessList.as_view(),
        name="project_access_list",
    ),
    path(
        "project-access/<pk>",
        views.ProjectAccessDetail.as_view(),
        name="project_access_detail",
    ),
    path(
        "task-accesses",
        views.TaskAccessList.as_view(),
        name="task_access_list",
    ),
    path(
        "task-access/<pk>",
        views.TaskAccessDetail.as_view(),
        name="task_access_detail",
    ),
    path("tasks", views.TaskList.as_view(), name="task_list"),
    path(
        "task-position-change/<pk>",
        views.TaskPositionChangeView.as_view(),
        name="task_position_change",
    ),
    path(
        "user-task-queue-position-change/<pk>",
        views.UserTaskQueuePositionChangeView.as_view(),
        name="user_task_queue_position_change",
    ),
    path("upload", views.UploadView.as_view(), name="upload"),
    path("task/<pk>", views.TaskDetail.as_view(), name="task_detail"),
    path(
        "task-start-work/<pk>",
        views.TaskStartWorkView.as_view(),
        name="task_start_work",
    ),
    path("task-close/<pk>", views.TaskCloseView.as_view(), name="task_close"),
    path(
        "task-unclose/<pk>",
        views.TaskUnCloseView.as_view(),
        name="task_unclose",
    ),
    path(
        "task-stop-work/<pk>",
        views.TaskStopWorkView.as_view(),
        name="task_stop_work",
    ),
    path("logs", views.LogList.as_view(), name="log_list"),
    path("comments", views.CommentList.as_view(), name="comment_list"),
    path("comment/<pk>", views.CommentDetail.as_view(), name="comment_detail"),
    path(
        "attachments", views.AttachmentList.as_view(), name="attachment_list"
    ),
    path(
        "attachment/<pk>",
        views.AttachmentDetail.as_view(),
        name="attachment_detail",
    ),
    path("dictionary", views.DictionaryView.as_view(), name="dictionary_view"),
    path("current-task", views.CurrentTaskView.as_view(), name="current_task"),
    path("notifications", views.NotificationAckListView.as_view(), name="notifications"),
    path("notification-confirm/<pk>", views.NotificationAckConfirmView.as_view(), name="confirm_notification"),
    path("user-task-queue", views.UserTaskQueueView.as_view(), name="user_task_queue"),
    path("user-task-queue-manage/<pk>", views.UserTaskQueueManageView.as_view(), name="user_task_queue"),
]
