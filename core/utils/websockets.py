import logging

import pusher
from django.conf import settings

logger = logging.getLogger(__name__)


class WebsocketHelper:
    @staticmethod
    def send(channel, event_name, data):
        if not settings.PUSHER_APP_SECRET:
            logger.debug("PUSHER_APP_SECRET not set")
            return

        try:
            pusher_client = pusher.Pusher(
                app_id=settings.PUSHER_APP_ID,
                key=settings.PUSHER_APP_KEY,
                secret=settings.PUSHER_APP_SECRET,
                host=settings.PUSHER_HOST,
            )

            pusher_client.trigger(
                channel,
                event_name,
                data,
            )
        except Exception as ex:
            logger.exception(f"Pusher exception: {ex}")
