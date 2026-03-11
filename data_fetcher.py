"""
Data fetching module for market data and news.
Handles candle data retrieval and news/event feeds.
"""

import datetime as dt
import pandas as pd
import numpy as np
import yfinance as yf
from config import PAIRS, PAIR_CURRENCIES, SESSIONS


def fetch_candle_data(pair: str, period: str = "3mo", interval: str = "1h") -> pd.DataFrame:
    """
    Fetch OHLCV candle data from Yahoo Finance.

    Args:
        pair: One of the supported pair keys (e.g. "EURUSD")
        period: How far back to pull data (default 3 months for monthly levels)
        interval: Candle interval (default 1h)

    Returns:
        DataFrame with columns: Open, High, Low, Close, Volume
    """
    ticker = PAIRS[pair]
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False)
        if df.empty:
            return _generate_fallback_data(pair)
        # Flatten multi-level columns if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.index = pd.to_datetime(df.index)
        # Remove timezone info for simpler handling
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        return df
    except Exception:
        return _generate_fallback_data(pair)


def fetch_daily_data(pair: str, period: str = "6mo") -> pd.DataFrame:
    """Fetch daily candles for higher-timeframe analysis."""
    ticker = PAIRS[pair]
    try:
        df = yf.download(ticker, period=period, interval="1d", progress=False)
        if df.empty:
            return _generate_fallback_daily(pair)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.index = pd.to_datetime(df.index)
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        return df
    except Exception:
        return _generate_fallback_daily(pair)


def _generate_fallback_data(pair: str) -> pd.DataFrame:
    """Generate synthetic fallback data when live feed is unavailable."""
    base_prices = {"EURUSD": 1.0850, "GBPUSD": 1.2650, "USDJPY": 149.50}
    base = base_prices.get(pair, 1.0)
    np.random.seed(42)

    periods = 500
    dates = pd.date_range(end=dt.datetime.utcnow(), periods=periods, freq="1h")
    noise = np.random.randn(periods).cumsum() * (base * 0.0005)
    close = base + noise
    high = close + np.abs(np.random.randn(periods)) * base * 0.0003
    low = close - np.abs(np.random.randn(periods)) * base * 0.0003
    open_ = close + np.random.randn(periods) * base * 0.0001

    return pd.DataFrame({
        "Open": open_, "High": high, "Low": low, "Close": close,
        "Volume": np.random.randint(100, 10000, periods),
    }, index=dates)


def _generate_fallback_daily(pair: str) -> pd.DataFrame:
    """Generate synthetic daily fallback data."""
    base_prices = {"EURUSD": 1.0850, "GBPUSD": 1.2650, "USDJPY": 149.50}
    base = base_prices.get(pair, 1.0)
    np.random.seed(99)

    periods = 120
    dates = pd.date_range(end=dt.datetime.utcnow(), periods=periods, freq="1D")
    noise = np.random.randn(periods).cumsum() * (base * 0.002)
    close = base + noise
    high = close + np.abs(np.random.randn(periods)) * base * 0.003
    low = close - np.abs(np.random.randn(periods)) * base * 0.003
    open_ = close + np.random.randn(periods) * base * 0.001

    return pd.DataFrame({
        "Open": open_, "High": high, "Low": low, "Close": close,
        "Volume": np.random.randint(1000, 50000, periods),
    }, index=dates)


def filter_session_data(df: pd.DataFrame, session: str) -> pd.DataFrame:
    """Filter candle data to the selected session hours (UTC)."""
    if session == "Day":
        return df
    start_hour, end_hour = SESSIONS[session]
    mask = (df.index.hour >= start_hour) & (df.index.hour < end_hour)
    return df[mask]


def fetch_news(pair: str) -> list[dict]:
    """
    Fetch news headlines related to the selected pair.

    Returns sample news data. Connect a news API for live headlines.
    """
    currencies = PAIR_CURRENCIES[pair]
    now = dt.datetime.utcnow()

    # Sample news data — structured for easy replacement with a real feed
    sample_news = [
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
    return sample_news


def fetch_upcoming_events(pair: str) -> list[dict]:
    """
    Fetch upcoming macro events for the pair's currencies.

    Sample data — replace with ForexFactory/Investing.com scraper
    or an economic calendar API for live events.
    """
    currencies = PAIR_CURRENCIES[pair]
    now = dt.datetime.utcnow()

    sample_events = [
        {
            "event": f"{currencies[1]} Interest Rate Decision",
            "currency": currencies[1],
            "datetime": (now + dt.timedelta(hours=6)).strftime("%Y-%m-%d %H:%M UTC"),
            "impact": "high",
            "forecast": "Hold",
        },
        {
            "event": f"{currencies[0]} Manufacturing PMI",
            "currency": currencies[0],
            "datetime": (now + dt.timedelta(hours=18)).strftime("%Y-%m-%d %H:%M UTC"),
            "impact": "medium",
            "forecast": "51.2",
        },
    ]
    return sample_events


def has_high_impact_news_soon(pair: str, hours_threshold: float = 2.0) -> tuple[bool, str]:
    """
    Check if high-impact news is approaching within the threshold.

    Returns:
        (is_blocking, description)
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
