from datetime import datetime, timedelta, timezone
from typing import List


def get_current_time() -> datetime:
    """
    Returns the current time in UTC.
    """
    return datetime.now(timezone.utc)

def get_week_start_end() -> List[datetime]:
    current_time = get_current_time().date()
    week_start = current_time - timedelta(
        days=current_time.weekday()
        )
    week_end = week_start + timedelta(
        days=6
        )
    return [week_start, week_end]