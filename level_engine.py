"""
Key levels computation module.
Computes day/week/month highs and lows from hourly candle data.
"""

import datetime as dt
import pandas as pd
from config import SESSIONS, PIP_MULTIPLIER


def compute_key_levels(df_hourly: pd.DataFrame, session: str) -> dict:
    """
    Compute key price levels from hourly data.
    Returns dict of level_name -> {"high": float, "low": float}
    """
    if df_hourly.empty:
        return {}

    now = df_hourly.index[-1]
    today = now.date()
    levels = {}

    # Current day
    today_data = df_hourly[df_hourly.index.date == today]
    if not today_data.empty:
        levels["Current Day"] = {
            "high": today_data["High"].max(),
            "low": today_data["Low"].min(),
        }

    # Previous day (skip weekends)
    prev_day = today - dt.timedelta(days=1)
    while prev_day.weekday() >= 5:
        prev_day -= dt.timedelta(days=1)
    prev_data = df_hourly[df_hourly.index.date == prev_day]
    if not prev_data.empty:
        levels["Previous Day"] = {
            "high": prev_data["High"].max(),
            "low": prev_data["Low"].min(),
        }

    # Current week (Monday-based)
    week_start = today - dt.timedelta(days=today.weekday())
    cw_data = df_hourly[df_hourly.index.date >= week_start]
    if not cw_data.empty:
        levels["Current Week"] = {
            "high": cw_data["High"].max(),
            "low": cw_data["Low"].min(),
        }

    # Previous week
    pw_start = week_start - dt.timedelta(days=7)
    pw_end = week_start - dt.timedelta(days=1)
    pw_data = df_hourly[(df_hourly.index.date >= pw_start) & (df_hourly.index.date <= pw_end)]
    if not pw_data.empty:
        levels["Previous Week"] = {
            "high": pw_data["High"].max(),
            "low": pw_data["Low"].min(),
        }

    # Current month
    month_start = today.replace(day=1)
    cm_data = df_hourly[df_hourly.index.date >= month_start]
    if not cm_data.empty:
        levels["Current Month"] = {
            "high": cm_data["High"].max(),
            "low": cm_data["Low"].min(),
        }

    # Previous month
    if month_start.month == 1:
        pm_start = month_start.replace(year=month_start.year - 1, month=12)
    else:
        pm_start = month_start.replace(month=month_start.month - 1)
    pm_end = month_start - dt.timedelta(days=1)
    pm_data = df_hourly[(df_hourly.index.date >= pm_start) & (df_hourly.index.date <= pm_end)]
    if not pm_data.empty:
        levels["Previous Month"] = {
            "high": pm_data["High"].max(),
            "low": pm_data["Low"].min(),
        }

    # Session high/low (today only, for selected session)
    if session != "Day":
        start_hour, end_hour = SESSIONS[session]
        session_mask = (
            (df_hourly.index.date == today) &
            (df_hourly.index.hour >= start_hour) &
            (df_hourly.index.hour < end_hour)
        )
        session_data = df_hourly[session_mask]
        if not session_data.empty:
            levels[f"{session} Session"] = {
                "high": session_data["High"].max(),
                "low": session_data["Low"].min(),
            }

    return levels


def levels_to_dataframe(levels: dict, current_price: float, pair: str) -> pd.DataFrame:
    """Convert levels dict to a display DataFrame with distance from current price."""
    pip_mult = PIP_MULTIPLIER.get(pair, 10000)
    rows = []
    for name, vals in levels.items():
        rows.append({
            "Level": name,
            "High": vals["high"],
            "Low": vals["low"],
            "Range (pips)": round((vals["high"] - vals["low"]) * pip_mult, 1),
            "Dist to High": round((vals["high"] - current_price) * pip_mult, 1),
            "Dist to Low": round((vals["low"] - current_price) * pip_mult, 1),
        })
    return pd.DataFrame(rows)
