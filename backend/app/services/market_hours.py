"""NSE trading hours: 09:15-15:30 IST, Monday-Friday.

Deliberately does not maintain an NSE holiday calendar — a real product
would, but for this build it's a documented simplification: on a market
holiday we'll just look "closed" a little early/inaccurately, which never
produces wrong prices, only a slightly imprecise 'market open' badge.
"""
from datetime import datetime, timezone, timedelta

IST = timezone(timedelta(hours=5, minutes=30))


def is_market_open(now: datetime | None = None) -> bool:
    now = (now or datetime.now(timezone.utc)).astimezone(IST)
    if now.weekday() >= 5:  # Sat/Sun
        return False
    open_t = now.replace(hour=9, minute=15, second=0, microsecond=0)
    close_t = now.replace(hour=15, minute=30, second=0, microsecond=0)
    return open_t <= now <= close_t
