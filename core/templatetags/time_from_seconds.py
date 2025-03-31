from django import template

from core.utils.time_from_seconds import time_from_seconds

register = template.Library()


@register.filter
def time_from_seconds_filter(seconds_value):
    hours, minutes, seconds = time_from_seconds(seconds_value)
    return f"{hours}h {minutes}m {seconds}s"
