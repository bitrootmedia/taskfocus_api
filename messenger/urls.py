from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import ThreadViewSet, MessageViewSet

router = DefaultRouter()
router.register(r"threads", ThreadViewSet, basename="thread")
router.register(
    r"threads/(?P<thread_id>[^/.]+)/messages",
    MessageViewSet,
    basename="message",
)

urlpatterns = [
    path("", include(router.urls)),
]
