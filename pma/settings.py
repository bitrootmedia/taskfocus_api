import logging
import os
from pathlib import Path

import environ
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

logger = logging.getLogger(__name__)
env = environ.Env(DEBUG=(bool, False))

BASE_DIR = Path(__file__).resolve().parent.parent
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))
SECRET_KEY = env("SECRET_KEY", default="SETMEUP")
DEBUG = env("DEBUG", default=False)
ALLOWED_HOSTS = env("ALLOWED_HOSTS", default="localhost,127.0.0.1,0.0.0.0").split(",")
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # 3rd-party
    "django_extensions",
    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    "dj_rest_auth",
    "simple_history",
    "silk",
    # local
    "apis",
    "core",
    "apps.messenger",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",  # automatically track user for history
    "silk.middleware.SilkyMiddleware",
]

CORS_ALLOWED_ORIGINS = env(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:3000,http://localhost:8000,http://127.0.0.1:3000",
).split(",")

# CSRF_TRUSTED_ORIGINS = env(
#     "CSRF_TRUSTED_ORIGINS", default="http://localhost:3000,http://127.0.0.1:3000"
# ).split(",")

ROOT_URLCONF = "pma.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "pma.wsgi.application"

DATABASES = {
    "default": env.db(
        "DATABASE_CONNECTION_STRING",
        default=f"sqlite:///{BASE_DIR}/db.sqlite3",
    ),
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

AUTH_USER_MODEL = "core.User"
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
# STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
# STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "apis.paginations.CustomPagination",
    "PAGE_SIZE": 20,
}

REST_AUTH_SERIALIZERS = {
    "PASSWORD_RESET_SERIALIZER": "apis.auth_serializers.CustomPasswordResetSerializer",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Project Management API",
    "DESCRIPTION": "PM",
    "VERSION": "0.1.0",
}

DEFAULT_FILE_STORAGE = env("DEFAULT_FILE_STORAGE", default="")
AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME", default="")
AWS_S3_ENDPOINT_URL = env("AWS_S3_ENDPOINT_URL", default="")
AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID", default="")
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY", default="")
AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME", default="")
AWS_QUERYSTRING_AUTH = False
AWS_DEFAULT_ACL = "public-read"

EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env("EMAIL_PORT", default="")
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="")
WEB_APP_URL = env("WEB_APP_URL", default="https://SETMEUP.com")
PUSHOVER_TOKEN = env("PUSHOVER_TOKEN", default="")
NOTIFIER_URL = env("NOTIFIER_URL", default="")
NOTIFIER_TOKEN = env("NOTIFIER_TOKEN", default="")
REQUESTS_CONNECT_TIMEOUT = 3
REQUESTS_READ_TIMEOUT = 3

PUSHER_APP_ID = env("PUSHER_APP_ID", default="")
PUSHER_HOST = env("PUSHER_HOST", default="")
PUSHER_APP_SECRET = env("PUSHER_APP_SECRET", default="")
PUSHER_APP_KEY = env("PUSHER_APP_KEY", default="")


LOGGING_LEVEL = env.str("LOGGING_LEVEL", default="WARNING")
LOGGING_FORMATTER = "verbose"
LOGGING_HANDLERS = ["console", "file"]
LOGGING_FILENAME = env.str("LOGGING_FILENAME", default="/tmp/django.log")
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": LOGGING_FORMATTER,
        },
        "file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "when": "d",
            "backupCount": 9,
            "filename": LOGGING_FILENAME,
            "formatter": LOGGING_FORMATTER,
            "level": LOGGING_LEVEL,
        },
    },
    "loggers": {
        "": {
            "handlers": LOGGING_HANDLERS,
            "level": LOGGING_LEVEL,
            "propagate": False,
        },
        "django": {
            "handlers": LOGGING_HANDLERS,
            "level": LOGGING_LEVEL,
            "propagate": False,
        },
        "django.server": {
            "handlers": LOGGING_HANDLERS,
            "level": LOGGING_LEVEL,
            "propagate": False,
        },
        "celery": {
            "handlers": LOGGING_HANDLERS,
            "level": LOGGING_LEVEL,
            "propagate": False,
        },
        "sentry_sdk.errors": {
            "handlers": LOGGING_HANDLERS,
            "level": LOGGING_LEVEL,
            "propagate": False,
        },
    },
    "root": {
        "handlers": LOGGING_HANDLERS,
        "level": LOGGING_LEVEL,
    },
}

STORAGES = {
    "default": {
        "BACKEND": DEFAULT_FILE_STORAGE,
    },
    "staticfiles": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
}

SENTRY_DSN = env.str("SENTRY_DSN", default=None)
SENTRY_ENVIRONMENT = env.str("SENTRY_ENVIRONMENT", default="production")
if SENTRY_DSN is not None:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.0,
    )
else:
    sentry_sdk.init(None)
    logger.warning("WARNING Sentry disabled.")


CREATE_BEACONS_INTERVAL_TIME_MIN = env.int("CREATE_BEACONS_INTERVAL_TIME_MIN", default=30)
CREATE_BEACONS_INTERVAL_TIME_MAX = env.int("CREATE_BEACONS_INTERVAL_TIME_MAX", default=60)
CREATE_BEACONS_ALLOWED_CLICK_TIME = env.int("CREATE_BEACONS_ALLOWED_CLICK_TIME", default=60)
