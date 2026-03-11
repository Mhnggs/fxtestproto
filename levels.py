"""
Key levels calculation and breach detection module.
Identifies important highs/lows and detects breaches.
"""

import datetime as dt
import pandas as pd
import numpy as np
from config import SESSIONS


def compute_key_levels(df_hourly: pd.DataFrame, session: str) -> dict:
    """
    Compute key price levels from hourly data.

    Returns dict of level_name -> {"high": float, "low": float}
    """
    now = df_hourly.index[-1] if len(df_hourly) > 0 else dt.datetime.utcnow()
    today = now.date()
    levels = {}

    # Current day
    today_data = df_hourly[df_hourly.index.date == today]
    if not today_data.empty:
        levels["Current Day"] = {
            "high": today_data["High"].max(),
            "low": today_data["Low"].min(),
        }

    # Previous day
    prev_day = today - dt.timedelta(days=1)
    # Skip weekends
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

    # Session high/low (today only)
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


def levels_to_dataframe(levels: dict) -> pd.DataFrame:
    """Convert levels dict to a display-friendly DataFrame."""
    rows = []
    for name, vals in levels.items():
        rows.append({
            "Level": name,
            "High": vals["high"],
            "Low": vals["low"],
            "Range": vals["high"] - vals["low"],
        })
    return pd.DataFrame(rows)


def detect_breaches(df: pd.DataFrame, levels: dict, lookback_bars: int = 24) -> list[dict]:
    """
    Detect breaches of key levels in recent candles.

    For each level high/low, checks if recent candles breached it and
    determines breach type (wick vs close) and direction.

    Args:
        df: Hourly candle data
        levels: Key levels dict from compute_key_levels
        lookback_bars: How many recent bars to scan

    Returns:
        List of breach event dicts
    """
    if len(df) < 2:
        return []

    recent = df.iloc[-lookback_bars:]
    breaches = []

    for level_name, vals in levels.items():
        high_level = vals["high"]
        low_level = vals["low"]

        for idx, row in recent.iterrows():
            # Check breach above high level
            if row["High"] >= high_level:
                breach_type = "close" if row["Close"] >= high_level else "wick"
                breaches.append({
                    "level": f"{level_name} High",
                    "level_price": high_level,
                    "direction": "above",
                    "breach_type": breach_type,
                    "candle_close": row["Close"],
                    "time": idx.strftime("%Y-%m-%d %H:%M"),
                })

            # Check breach below low level
            if row["Low"] <= low_level:
                breach_type = "close" if row["Close"] <= low_level else "wick"
                breaches.append({
                    "level": f"{level_name} Low",
                    "level_price": low_level,
                    "direction": "below",
                    "breach_type": breach_type,
                    "candle_close": row["Close"],
                    "time": idx.strftime("%Y-%m-%d %H:%M"),
                })

    # Deduplicate: keep only the most recent breach per level
    seen = {}
    for b in breaches:
        key = b["level"]
        if key not in seen or b["time"] > seen[key]["time"]:
            seen[key] = b

    return sorted(seen.values(), key=lambda x: x["time"], reverse=True)


def interpret_breaches(breaches: list[dict]) -> dict:
    """
    Summarize breach behavior into a directional signal component.

    Returns:
        {"bias": "bullish"|"bearish"|"neutral", "reason": str}
    """
    if not breaches:
        return {"bias": "neutral", "reason": "No recent breaches detected"}

    bullish_signals = 0
    bearish_signals = 0
    reasons = []

    for b in breaches:
        if b["direction"] == "below" and b["breach_type"] == "wick":
            # Wick below key low then reclaim = bullish
            bullish_signals += 1
            reasons.append(f"wick below {b['level']} then reclaimed")
        elif b["direction"] == "above" and b["breach_type"] == "wick":
            # Wick above key high then reject = bearish
            bearish_signals += 1
            reasons.append(f"wick above {b['level']} then rejected")
        elif b["direction"] == "above" and b["breach_type"] == "close":
            # Close above key high = bullish continuation
            bullish_signals += 1
            reasons.append(f"closed above {b['level']}")
        elif b["direction"] == "below" and b["breach_type"] == "close":
            # Close below key low = bearish continuation
            bearish_signals += 1
            reasons.append(f"closed below {b['level']}")

    if bullish_signals > bearish_signals:
        return {"bias": "bullish", "reason": "; ".join(reasons[:3])}
    elif bearish_signals > bullish_signals:
        return {"bias": "bearish", "reason": "; ".join(reasons[:3])}
    else:
        return {"bias": "neutral", "reason": "mixed breach signals"}
