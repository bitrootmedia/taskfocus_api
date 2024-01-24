import datetime
from django import template

from time import gmtime
from time import strftime

register = template.Library()


@register.filter
def time_from_seconds(value):
    # NOTE: The following resets if it goes over 23:59:59
    return strftime("%H:%M:%S", gmtime(value))