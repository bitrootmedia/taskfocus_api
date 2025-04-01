import typing

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import URLPattern, URLResolver, include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from apps.admin_panel.forms import StyledLoginForm

from .views import index as index_view

URL = typing.Union[URLPattern, URLResolver]
URLList = typing.List[URL]
urlpatterns: URLList = []

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


urlpatterns += [
    path("", index_view, name="index"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="auth/login.html", authentication_form=StyledLoginForm),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(next_page="/login/"), name="logout"),
    path("silk/", include("silk.urls", namespace="silk")),
    path("api/", include("apis.urls")),
    path("api/auth/", include("dj_rest_auth.urls")),
    # path("api-auth/", include("rest_framework.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/schema/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
    path(
        "api/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("admin-panel/", include("apps.admin_panel.urls")),
    path("messenger/", include("apps.messenger.urls")),
    path("", admin.site.urls),
]
