"""
Key levels computation with breach-aware status tracking.
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


def classify_level_status(
    level_price: float, side: str, current_price: float,
    breaches: list[dict], level_name_fragment: str,
) -> str:
    """
    Determine the status of a specific level relative to current price and breaches.
    Returns: untouched, breached, reclaimed, active resistance, active support
    """
    match_key = f"{level_name_fragment} {'High' if side == 'high' else 'Low'}"
    breach = None
    for b in breaches:
        if b["level"] == match_key:
            breach = b
            break

    if breach is None:
        if side == "high":
            return "active resistance" if current_price < level_price else "untouched"
        else:
            return "active support" if current_price > level_price else "untouched"

    interp = breach.get("interpretation", "")
    if interp == "Breakout":
        return "breached"
    elif interp in ("Reclaim", "Liquidity Sweep"):
        return "reclaimed"
    return "breached"


def build_level_rows(levels: dict, current_price: float, pair: str, breaches: list[dict]) -> list[dict]:
    """
    Build a flat list of individual level rows (each high and low separately)
    with price, distance, and breach status.
    """
    pip_mult = PIP_MULTIPLIER.get(pair, 10000)
    rows = []

    for name, vals in levels.items():
        for side in ["high", "low"]:
            price = vals[side]
            dist = round((price - current_price) * pip_mult, 1)
            status = classify_level_status(price, side, current_price, breaches, name)
            label = f"{name} {'High' if side == 'high' else 'Low'}"
            rows.append({
                "level": label,
                "price": price,
                "distance_pips": dist,
                "status": status,
            })

    return rows
