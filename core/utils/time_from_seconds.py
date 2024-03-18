def time_from_seconds(seconds_value):
    minutes, seconds = divmod(seconds_value, 60)
    hours, minutes = divmod(minutes, 60)
    return hours, minutes, seconds