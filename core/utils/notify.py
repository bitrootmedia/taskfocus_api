from django.core.mail import send_mail
import logging
logger = logging.getLogger(__name__)


def notify_user(user, title, message):
    if user.email:
        send_mail(
            title,
            message,
            None,
            [user.email],
            fail_silently=True,
        )
