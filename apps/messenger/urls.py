from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import ThreadViewSet, MessageViewSet, MessageAckViewSet

router = DefaultRouter()
router.register(r"threads", ThreadViewSet, basename="thread")
router.register(
    r"threads/(?P<thread_id>[^/.]+)/messages",
    MessageViewSet,
    basename="message",
)

urlpatterns = [
    path("", include(router.urls)),
    path("messages/ack/", MessageAckViewSet.as_view({"post": "ack_messages"}), name="ack-messages"),
]
