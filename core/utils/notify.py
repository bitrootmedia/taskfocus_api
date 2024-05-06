from django.core.mail import send_mail
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def notify_user(
    user, notification, message=None, title="You've got a new notification"
):
    if notification:
        message = f"{settings.WEB_APP_URL}/dashboard/notifications/?id={notification.id}"

    # this should go to celery
    if user.email:
        send_mail(
            title,
            message,
            None,
            [user.email],
            fail_silently=True,
        )

    if user.pushover_user:
        try:
            rx = requests.post(
                "https://api.pushover.net/1/messages.json",
                data={
                    "token": settings.PUSHOVER_TOKEN,
                    "user": user.pushover_user,
                    "title": title,
                    "message": message,
                },
                timeout=(3, 3),
            )
            logger.debug(rx.text)
        except Exception as ex:
            logger.exception(f"{ex}")

    if (
        user.notifier_user
        and settings.NOTIFIER_URL
        and settings.NOTIFIER_TOKEN
    ):
        url = f"{settings.NOTIFIER_URL}/api/messages/"
        tag = f"ayeaye:notification-{user.username}"

        payload = {
            "tag": tag,
            "title": title,
            "content": message,
            "level": "HIGH",
        }

        try:
            requests.post(
                url,
                json=payload,
                auth=(
                    "",
                    settings.NOTIFIER_TOKEN,
                ),
                timeout=(
                    settings.REQUESTS_CONNECT_TIMEOUT,
                    settings.REQUESTS_READ_TIMEOUT,
                ),
            )
        except Exception as exc:
            logger.exception(
                f"Call with payload {payload} to {url} timed out. {exc}"
            )
