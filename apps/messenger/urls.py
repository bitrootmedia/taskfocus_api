from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import ThreadViewSet, MessageViewSet, DirectThreadViewSet

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
