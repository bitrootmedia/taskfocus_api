from django.urls import path

from .views import UserCreateView, UserDeleteView, UserListView, UserUpdateView

urlpatterns = [
    path("", UserListView.as_view(), name="user-list"),
    path("create/", UserCreateView.as_view(), name="user-create"),
    path("<uuid:pk>/edit/", UserUpdateView.as_view(), name="user-update"),
    path("<uuid:pk>/delete/", UserDeleteView.as_view(), name="user-delete"),
]
