from time import gmtime, strftime

from django import template

register = template.Library()


@register.filter
def time_from_seconds(value):
    # NOTE: The following resets if it goes over 23:59:59
    return strftime("%H:%M:%S", gmtime(value))