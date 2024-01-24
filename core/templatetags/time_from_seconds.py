from django import template

register = template.Library()


@register.filter
def time_from_seconds(seconds_value):
    minutes, seconds = divmod(seconds_value, 60)
    hours, minutes = divmod(minutes, 60)
    
    return f"{hours}h {minutes}m {seconds}s"