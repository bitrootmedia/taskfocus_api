import datetime
import logging
import uuid
from argparse import ArgumentTypeError

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import validate_email

from core.models import User
from core.utils.send_user_report import send_user_report

logger = logging.getLogger(__name__)


def valid_uuid4(s: str):
    try:
        return uuid.UUID(s, version=4)
    except ValueError:
        raise ArgumentTypeError(f"Ivalid UUID4: {s}")


def valid_date(s: str) -> datetime.datetime:
    try:
        return datetime.datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        raise ArgumentTypeError(f"Invalid date: {s}")


def valid_email(s: str):
    try:
        validate_email(s)  # returns nothing on success
        return s
    except ValidationError:
        raise ArgumentTypeError(f"Invalid recipient email: {s}")


class Command(BaseCommand):
    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            "-u",
            "--username",
            help="Username of the user.",
            type=str,
        )

        group.add_argument(
            "-id",
            "--user_id",
            help="ID of the user.",
            type=valid_uuid4,
        )

        parser.add_argument(
            "-s",
            "--start_date",
            help="Start date in format YYYY-MM-DD",
            required=True,
            type=valid_date
        )

        parser.add_argument(
            "-e",
            "--end_date",
            help="End date in format YYYY-MM-DD",
            required=True,
            type=valid_date
        )

        parser.add_argument(
            "-r",
            "--recipient",
            help="Recipient of the report email",
            required=True,
            type=valid_email
        )

        parser.add_argument(
            "-l",
            "--period_label",
            help="Period label for the report dates (4ex. daily, weekly, etc.)",
            required=True,
            type=str
        )

    def handle(self, *args, **options):
        try:
            if options.get("user_id"):
                user = User.objects.get(id=options["user_id"])
            else:
                user = User.objects.get(username=options["username"])
        except User.DoesNotExist:
            raise CommandError("User does not exist for given " + "user_id" if options.get("user_id") else "uuid4")
        except User.MultipleObjectsReturned:
            raise CommandError("Multiple users exist for given " + 'user_id' if options.get("user_id") else "uuid4")

        send_user_report(
            options["start_date"],
            options["end_date"],
            user.email,
            options["period_label"],
            user_id=user.id
        )
