from django.urls import path

from .views import TaskCreateView, TaskDeleteView, TaskListView, TaskUpdateView

urlpatterns = [
    path("", TaskListView.as_view(), name="task-list"),
    path("create/", TaskCreateView.as_view(), name="task-create"),
    path("<uuid:pk>/edit/", TaskUpdateView.as_view(), name="task-update"),
    path("<uuid:pk>/delete/", TaskDeleteView.as_view(), name="task-delete"),
]
