"""Numbers, durations and dates as text. No GTK."""
from datetime import date, timedelta


def number(value, digits=0):
    """1234.5 -> '1,235'; with digits, '1,234.5'."""
    return f"{value:,.{digits}f}"


def duration(value):
    """timedelta -> '7 h 12 min', '45 min'."""
    minutes = round(value.total_seconds() / 60)
    hours, minutes = divmod(minutes, 60)
    if hours and minutes:
        return f"{hours} h {minutes} min"
    if hours:
        return f"{hours} h"
    return f"{minutes} min"


def hours(value):
    """timedelta -> hours as a float (for charts)."""
    return value.total_seconds() / 3600


def clock(value):
    return value.strftime("%H:%M")


def day(value, today=None):
    """'Today', 'Yesterday', or 'Mon 2 Nov' (with the year if not this
    year)."""
    today = today or date.today()
    if value == today:
        return "Today"
    if value == today - timedelta(days=1):
        return "Yesterday"
    text = f"{value:%a} {value.day} {value:%b}"
    return text if value.year == today.year else f"{text} {value.year}"


def short_day(value):
    """'2 Nov'."""
    return f"{value.day} {value:%b}"


def ago(moment, now):
    """How long ago, for 'last synced': 'just now', '25 min ago',
    '3 h ago', 'Yesterday 21:40', '2 Nov 21:40'."""
    seconds = (now - moment).total_seconds()
    if seconds < 120:
        return "just now"
    if seconds < 3600:
        return f"{int(seconds // 60)} min ago"
    if moment.date() == now.date():
        return f"{int(seconds // 3600)} h ago"
    return f"{day(moment.date(), now.date())} {clock(moment)}"


def duration_hours(value):
    """Hours as a float -> '7 h 12 min'."""
    return duration(timedelta(hours=value))
