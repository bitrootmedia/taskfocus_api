from django.urls import include, path

from .views import AdminPanelHomeView

urlpatterns = [
    path("users/", include("apps.admin_panel.users.urls")),
    path("tasks/", include("apps.admin_panel.tasks.urls")),
    path("", AdminPanelHomeView.as_view(), name="admin-panel-home"),
]
