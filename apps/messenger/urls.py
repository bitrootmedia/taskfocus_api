from django.urls import path

from .api import ThreadView, ThreadViewByUser, UnreadThreadsView, UserThreadsView

urlpatterns = [
    path("users", UserThreadsView.as_view(), name="users"),
    path("unread-threads", UnreadThreadsView.as_view(), name="unread-threads"),
    path("threads/<uuid:user_id>", ThreadViewByUser.as_view(), name="thread-by-user"),
    path("conversations/<uuid:thread_id>", ThreadView.as_view(), name="thread"),
]
