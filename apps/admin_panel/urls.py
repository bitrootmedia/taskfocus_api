from django.urls import include, path

from .views import AdminPanelHomeView, admin_panel_logout

urlpatterns = [
    path("users/", include("apps.admin_panel.users.urls")),
    path("tasks/", include("apps.admin_panel.tasks.urls")),
    path("logout/", view=admin_panel_logout, name="logout"),
    path("", AdminPanelHomeView.as_view(), name="admin-panel-home"),
]
