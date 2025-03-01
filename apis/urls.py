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
        "task-total-time/<pk>",
        views.TaskTotalTime.as_view(),
        name="task_total_time",
    ),
    path(
        "user-task-queue-position-change/<pk>",
        views.UserTaskQueuePositionChangeView.as_view(),
        name="user_task_queue_position_change",
    ),
    path("upload", views.UploadView.as_view(), name="upload"),
    path("task/<pk>", views.TaskDetail.as_view(), name="task_detail"),
    path(
        "task-block-list/<task>",
        views.TaskBlockListV2.as_view(),
        name="task_block_list",
    ),
    path(
        "task-block-create/",
        views.TaskBlockCreate.as_view(),
        name="task_block_create",
    ),
    path(
        "task-block-update/",
        views.TaskBlockUpdate.as_view(),
        name="task_block_update",
    ),
    path(
        "task-block-delete/",
        views.TaskBlockDelete.as_view(),
        name="task_block_delete",
    ),
    path(
        "task-block-move/",
        views.TaskBlockMove.as_view(),
        name="task_block_move",
    ),
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
    path(
        "task-sessions",
        views.TaskSessionList.as_view(),
        name="task_sessions_list",
    ),
    path(
        "task-session/<pk>",
        views.TaskSessionDetail.as_view(),
        name="task_sessions_detail",
    ),
    path("comment/<pk>", views.CommentDetail.as_view(), name="comment_detail"),
    path("notes", views.NoteList.as_view(), name="note_list"),
    path("note/<pk>", views.NoteDetail.as_view(), name="note_detail"),
    path(
        "private-notes",
        views.PrivateNoteList.as_view(),
        name="private_note_list",
    ),
    path(
        "private-note/<pk>",
        views.PrivateNoteDetail.as_view(),
        name="private_note_detail",
    ),
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
    path(
        "notifications",
        views.NotificationAckListView.as_view(),
        name="notifications",
    ),
    path(
        "notification-confirm/<pk>",
        views.NotificationAckConfirmView.as_view(),
        name="confirm_notification",
    ),
    path(
        "user-task-queue",
        views.UserTaskQueueView.as_view(),
        name="user_task_queue",
    ),
    path(
        "user-task-queue-manage/<pk>",
        views.UserTaskQueueManageView.as_view(),
        name="user_task_queue_manage",
    ),
    path("reminders", views.ReminderListView.as_view(), name="reminder_list"),
    path(
        "reminder-close/<pk>",
        views.ReminderCloseView.as_view(),
        name="reminder_close",
    ),
    path(
        "change-task-owner/<pk>",
        views.ChangeTaskOwnerView.as_view(),
        name="task_owner_change",
    ),
    path(
        "change-project-owner/<pk>",
        views.ChangeProjectOwnerView.as_view(),
        name="project_owner_change",
    ),
    path(
        "work_session_breakdown",
        views.WorkSessionsBreakdownView.as_view(),
        name="work_sessions_breakdown",
    ),
    path(
        "pinned-tasks",
        views.PinnedTaskList.as_view(),
        name="pinned_task_list",
    ),
    path(
        "pin-task/<task_id>",
        views.PinTaskDetail.as_view(),
        name="pin_task_detail",
    ),
    path(
        "pinned-boards",
        views.PinnedBoardList.as_view(),
        name="pinned_board_list",
    ),
    path(
        "pin-board/<board_id>",
        views.PinBoardDetail.as_view(),
        name="pin_board_detail",
    ),
    path(
        "boards",
        views.BoardList.as_view(),
        name="board_list",
    ),
    path(
        "board/<pk>",
        views.BoardDetail.as_view(),
        name="board_detail",
    ),
    path(
        "board/logs/<pk>", views.BoardLogList.as_view(), name="board_log_list"
    ),
    path(
        "board-users/<uuid:board_id>",
        views.BoardUserView.as_view(),
        name="board_users",
    ),
    path("card-create", views.CardCreate.as_view(), name="card_create"),
    path("card-detail/<pk>", views.CardDetail.as_view(), name="card_detail"),
    path("card-move", views.CardMove.as_view(), name="card_move"),
    path(
        "card-item-create",
        views.CardItemCreate.as_view(),
        name="card_item_create",
    ),
    path(
        "card-item-detail/<pk>",
        views.CardItemDetail.as_view(),
        name="card_item_detail",
    ),
    path(
        "card-item-move", views.CardItemMove.as_view(), name="card_item_move"
    ),
]
