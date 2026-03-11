"""
News and economic calendar engine.
Uses sample data — connect a real news API for live headlines.
"""

import datetime as dt
from config import PAIR_CURRENCIES


def fetch_news(pair: str) -> list[dict]:
    """
    Fetch news headlines for the selected pair's currencies.
    Sample data — replace with NewsAPI / ForexFactory RSS for live feeds.
    """
    currencies = PAIR_CURRENCIES[pair]
    now = dt.datetime.utcnow()

    return [
        {
            "headline": f"{currencies[0]}/{currencies[1]}: Central bank commentary drives volatility",
            "currency": currencies[0],
            "timestamp": (now - dt.timedelta(hours=2)).strftime("%Y-%m-%d %H:%M UTC"),
            "impact": "medium",
            "source": "Reuters (sample)",
        },
        {
            "headline": f"{currencies[1]} economic data release ahead",
            "currency": currencies[1],
            "timestamp": (now - dt.timedelta(hours=1)).strftime("%Y-%m-%d %H:%M UTC"),
            "impact": "high",
            "source": "Bloomberg (sample)",
        },
        {
            "headline": f"Market sentiment shifts on {currencies[0]} outlook",
            "currency": currencies[0],
            "timestamp": (now - dt.timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M UTC"),
            "impact": "low",
            "source": "FX Wire (sample)",
        },
    ]


def fetch_upcoming_events(pair: str) -> list[dict]:
    """
    Fetch upcoming macro events for the pair's currencies.
    Sample data — replace with economic calendar API for live events.
    """
    currencies = PAIR_CURRENCIES[pair]
    now = dt.datetime.utcnow()

    return [
        {
            "event": f"{currencies[1]} Interest Rate Decision",
            "currency": currencies[1],
            "datetime": (now + dt.timedelta(hours=6)).strftime("%Y-%m-%d %H:%M UTC"),
            "impact": "high",
            "forecast": "Hold",
            "time_until": "6h 00m",
        },
        {
            "event": f"{currencies[0]} Manufacturing PMI",
            "currency": currencies[0],
            "datetime": (now + dt.timedelta(hours=18)).strftime("%Y-%m-%d %H:%M UTC"),
            "impact": "medium",
            "forecast": "51.2",
            "time_until": "18h 00m",
        },
    ]


def has_high_impact_news_soon(pair: str, hours_threshold: float = 2.0) -> tuple[bool, str]:
    """
    Check if high-impact news is approaching within the threshold.
    Returns (is_blocking, description).
    """
    events = fetch_upcoming_events(pair)
    now = dt.datetime.utcnow()

    for event in events:
        if event["impact"] == "high":
            event_time = dt.datetime.strptime(event["datetime"], "%Y-%m-%d %H:%M UTC")
            diff_hours = (event_time - now).total_seconds() / 3600
            if 0 < diff_hours <= hours_threshold:
                return True, f"{event['event']} in {diff_hours:.1f}h"

    return False, ""


def get_news_risk_status(pair: str) -> dict:
    """
    Determine overall news risk status.

    Returns {"status": "Clear"|"Caution"|"Block", "next_event": str, "time_until": str}
    """
    events = fetch_upcoming_events(pair)
    now = dt.datetime.utcnow()

    nearest_high = None
    nearest_hours = float("inf")

    for event in events:
        event_time = dt.datetime.strptime(event["datetime"], "%Y-%m-%d %H:%M UTC")
        diff_hours = (event_time - now).total_seconds() / 3600
        if diff_hours > 0 and event["impact"] == "high" and diff_hours < nearest_hours:
            nearest_high = event
            nearest_hours = diff_hours

    if nearest_high is None:
        return {"status": "Clear", "next_event": "None scheduled", "time_until": "-"}

    if nearest_hours <= 1.0:
        status = "Block"
    elif nearest_hours <= 3.0:
        status = "Caution"
    else:
        status = "Clear"

    hours = int(nearest_hours)
    minutes = int((nearest_hours - hours) * 60)

    return {
        "status": status,
        "next_event": nearest_high["event"],
        "time_until": f"{hours}h {minutes:02d}m",
    }
