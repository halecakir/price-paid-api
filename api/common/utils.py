import calendar
from datetime import datetime

from .exceptions import IllegalDateError


def from_year_month_to_datetime(date_str, last_day=False):
    date = None
    try:
        year, month = date_str.split("-")
        day = "01"
        if last_day:
            day = calendar.monthrange(int(year), int(month))[1]

        date = datetime.strptime(f"{year}-{month}-{day}", "%Y-%m-%d")
    except Exception:
        raise IllegalDateError(date_str)
    return date
