def time_from_seconds(seconds_value):
    if not seconds_value:  # tmp - might change later
        return 0, 0, 0

    minutes, seconds = divmod(seconds_value, 60)
    hours, minutes = divmod(minutes, 60)
    return hours, minutes, seconds
