from django.urls import path

from .views import TaskListView, UserListView, admin_dashboard, task_edit, user_edit

app_name = "admin_panel"

urlpatterns = [
    path("", admin_dashboard, name="dashboard"),  # Strona główna panelu admina
    path("users/", UserListView.as_view(), name="user_list"),
    path("users/<int:pk>/edit/", user_edit, name="user_edit"),
    path("tasks/", TaskListView.as_view(), name="task_list"),
    path("tasks/<int:pk>/edit/", task_edit, name="task_edit"),
]
