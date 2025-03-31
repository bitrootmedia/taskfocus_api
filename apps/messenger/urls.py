from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .api import DirectMessageViewSet, DirectThreadViewSet, MessageViewSet, ThreadViewSet

router = DefaultRouter()
router.register(r"threads", ThreadViewSet, basename="thread")
router.register(r"threads/(?P<thread_id>[^/.]+)/messages", MessageViewSet, basename="messages")
router.register(r"direct-threads", DirectThreadViewSet, basename="direct-thread")
router.register(r"direct-threads/(?P<thread_id>[^/.]+)/messages", DirectMessageViewSet, basename="direct-messages")


urlpatterns = [
    path("", include(router.urls)),
]
