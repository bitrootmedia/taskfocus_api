import datetime
import logging
from collections import defaultdict

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.db.models import F, Q, Sum
from django.template.loader import render_to_string

from core.models import TaskWorkSession, User

logger = logging.getLogger(__name__)


def _get_user(username, user_id):
    if not any([username, user_id]):
        raise ValueError("No username nor user_id provided")

    search_val = None

    if username and user_id:
        logger.warning("Username and user_id provided to fetch the user, using user_id")

    try:
        if user_id:
            search_val = user_id
            return User.objects.get(id=user_id)
        else:
            search_val = username
            return User.objects.get(username=username)
    except User.DoesNotExist:
        ValueError(f"User does not exist for : {search_val}")
    except User.MultipleObjectsReturned:
        ValueError(f"Multiple users exist for : {search_val}")

    raise ValueError(f"No user found for (user_id:{user_id} | username:{username})")


def _convert_dates(date):
    try:
        if isinstance(date, datetime.datetime):
            return date.date()

        if isinstance(date, datetime.date):
            return date

        return datetime.datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"Invalid date: {date}")


def _valid_email(email: str):
    try:
        validate_email(email)  # returns nothing on success
    except ValidationError:
        raise ValueError(f"Invalid recipient email: {email}")


def _get_email_subject(period_label, username, start_date, end_date):
    return f"{period_label.title()} user report: {username} : {start_date.strftime('%d-%m-%Y')}-{end_date.strftime('%d-%m-%Y')}",


def send_user_report(start_date, end_date, recipient, period_label, username=None, user_id=None):
    user = _get_user(username, user_id)

    start_date, end_date = _convert_dates(start_date), _convert_dates(end_date)

    _valid_email(recipient)

    work_sessions = TaskWorkSession.objects.filter(
        Q(started_at__date__gte=start_date)
        & Q(stopped_at__date__lte=end_date)
        & Q(user=user)
    )

    # NOTE: Should we send anything when no work has been done?
    if not work_sessions:
        logger.info(
            (
                f"No {period_label} work sessions found for {user} in period: "
                f"{start_date.strftime('%d-%m-%Y')}-{end_date.strftime('%d-%m-%Y')}"
            )
        )
        return

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

    sessions_by_day = dict(sessions_by_day)  # Convert to dict for DTL .items call

    message_content_html = render_to_string("user_report.html", {
        "total_time_sum": total_time_sum,
        "user": user,
        "start_date": start_date,
        "end_date": end_date,
        "sessions_by_day": sessions_by_day
    })

    send_mail(
        _get_email_subject(period_label, user.username, start_date, end_date),
        message_content_html,
        settings.DEFAULT_FROM_EMAIL,
        [recipient, ],
        fail_silently=True,
        html_message=message_content_html
    )

    logger.debug(message_content_html)
