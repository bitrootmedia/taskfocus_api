import datetime
import logging
import uuid
from argparse import ArgumentTypeError
from collections import defaultdict

from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import validate_email
from django.db.models import F, Q, Sum
from django.template.loader import render_to_string

from core.models import TaskWorkSession, User

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


def valid_email(s:str):
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
        
    def handle(self, *args, **options):
        try:
            if options.get("user_id"):
                user= User.objects.get(id=options["user_id"])
            else:
                user = User.objects.get(username=options["username"])
        except User.DoesNotExist:
            raise CommandError("User does not exist for given " +  "user_id" if options.get("user_id") else "uuid4")
        except User.MultipleObjectsReturned:
            raise CommandError("Multiple users exist for given " + 'user_id' if options.get("user_id") else "uuid4")
        
        work_sessions = TaskWorkSession.objects.filter(
            Q(started_at__date__gte=options["start_date"])
            & Q(stopped_at__date__lte=options["end_date"])
            & Q(user=user)
        )
        
        total_time_sum = work_sessions.aggregate(time_sum=Sum("total_time")).get("time_sum")
        
        work_sessions = work_sessions.annotate(
            date=F('started_at__date'), 
            task_name=F('task__title'),
            project_name=F('task__project__title'),
        ).order_by('date')

        # Create date -> entries map
        sessions_by_day = defaultdict(lambda: {"entries": [], "total": 0})
        for session in work_sessions:
            sessions_by_day[session.date]["entries"].append(session)
        
        # Calculate daily totals
        for date, day_data in sessions_by_day.items():
            sessions_by_day[date]["total"] = sum([entry.total_time for entry in day_data["entries"]])
        
        sessions_by_day = dict(sessions_by_day)  # Conver to dict for DTL .items call
        
        message_content_html = render_to_string("user_report.html", {
            "total_time_sum": total_time_sum, 
            "user": user,
            "start_date": options["start_date"],
            "end_date": options["end_date"],
            "sessions_by_day": sessions_by_day
        })
        
        send_mail(
            f"User report: {user.username}:{options['start_date'].date()}-{options['end_date'].date()}",
            message_content_html,
            None,
            [options['recipient'], ],
            fail_silently=False,
            html_message=message_content_html
        )
        
        logger.debug(message_content_html)