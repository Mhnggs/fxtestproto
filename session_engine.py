"""
Session engine: computes session-specific levels for all sessions.
"""

import datetime as dt
import pandas as pd
from config import SESSIONS, SESSION_LIST, PIP_MULTIPLIER


def compute_all_session_levels(df_hourly: pd.DataFrame, pair: str) -> dict:
    """
    Compute high/low/range for each trading session (today's data).

    Returns dict of session_name -> {"high", "low", "range_pips"}
    """
    if df_hourly.empty:
        return {}

    today = df_hourly.index[-1].date()
    pip_mult = PIP_MULTIPLIER.get(pair, 10000)
    result = {}

    for session_name in SESSION_LIST:
        start_hour, end_hour = SESSIONS[session_name]
        mask = (
            (df_hourly.index.date == today) &
            (df_hourly.index.hour >= start_hour) &
            (df_hourly.index.hour < end_hour)
        )
        session_data = df_hourly[mask]

        if session_data.empty:
            # Try previous trading day
            prev_day = today - dt.timedelta(days=1)
            while prev_day.weekday() >= 5:
                prev_day -= dt.timedelta(days=1)
            mask = (
                (df_hourly.index.date == prev_day) &
                (df_hourly.index.hour >= start_hour) &
                (df_hourly.index.hour < end_hour)
            )
            session_data = df_hourly[mask]

        if not session_data.empty:
            high = session_data["High"].max()
            low = session_data["Low"].min()
            result[session_name] = {
                "high": high,
                "low": low,
                "range_pips": round((high - low) * pip_mult, 1),
            }

    return result


def session_levels_to_rows(session_levels: dict, current_price: float, pair: str) -> list[dict]:
    """Convert session levels to display rows with distance from current price."""
    pip_mult = PIP_MULTIPLIER.get(pair, 10000)
    rows = []
    for name, vals in session_levels.items():
        rows.append({
            "Session": name,
            "High": vals["high"],
            "Low": vals["low"],
            "Range (pips)": vals["range_pips"],
            "Dist to High (pips)": round((vals["high"] - current_price) * pip_mult, 1),
            "Dist to Low (pips)": round((vals["low"] - current_price) * pip_mult, 1),
        })
    return rows
