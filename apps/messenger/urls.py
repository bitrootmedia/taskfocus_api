from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .api import DirectThreadViewSet, MessageViewSet, ThreadViewSet

router = DefaultRouter()
router.register(r"threads", ThreadViewSet, basename="thread")
router.register(
    r"threads/(?P<thread_id>[^/.]+)/messages",
    MessageViewSet,
    basename="message",
)
router.register(r"direct-threads", DirectThreadViewSet, basename="direct-thread")


urlpatterns = [
    path("", include(router.urls)),
]
