"""Date and period utilities."""

from datetime import datetime, timedelta

# Period options used across the application
PERIOD_OPTIONS = [
    "MTD",
    "QTD",
    "YTD",
    "Trailing 1-Year",
    "Trailing 3-Years",
    "Trailing 5-Years",
    "Trailing 10-Years",
    "Inception",
]


def get_period_dates(period: str, earliest_date: datetime, latest_date: datetime) -> tuple[datetime, datetime]:
    """Calculate start and end dates for a given period."""
    today = datetime.now().date()
    
    if period == "MTD":
        start = datetime(today.year, today.month, 1)
        end = datetime.now()
    elif period == "QTD":
        quarter = (today.month - 1) // 3 + 1
        start = datetime(today.year, (quarter - 1) * 3 + 1, 1)
        end = datetime.now()
    elif period == "YTD":
        start = datetime(today.year, 1, 1)
        end = datetime.now()
    elif period == "Trailing 1-Year":
        start = datetime.now() - timedelta(days=365)
        end = datetime.now()
    elif period == "Trailing 3-Years":
        start = datetime.now() - timedelta(days=3 * 365)
        end = datetime.now()
    elif period == "Trailing 5-Years":
        start = datetime.now() - timedelta(days=5 * 365)
        end = datetime.now()
    elif period == "Trailing 10-Years":
        start = datetime.now() - timedelta(days=10 * 365)
        end = datetime.now()
    elif period == "Inception":
        start = earliest_date
        end = latest_date
    else:
        start = earliest_date
        end = latest_date
    
    return start, end
