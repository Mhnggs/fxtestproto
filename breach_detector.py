"""
Breach detection and liquidity sweep identification.
Scans recent candles for interactions with key levels.
"""

import pandas as pd


def detect_breaches(df: pd.DataFrame, levels: dict, lookback_bars: int = 24) -> list[dict]:
    """
    Detect breaches of key levels in recent candles.
    Classifies each as wick or close breach and assigns an interpretation.
    """
    if len(df) < 2:
        return []

    recent = df.iloc[-lookback_bars:]
    breaches = []

    for level_name, vals in levels.items():
        high_level = vals["high"]
        low_level = vals["low"]

        for idx, row in recent.iterrows():
            # Breach above high level
            if row["High"] >= high_level:
                breach_type = "Close" if row["Close"] >= high_level else "Wick"
                interpretation = _classify_breach("above", breach_type, row, high_level)
                breaches.append({
                    "level": f"{level_name} High",
                    "level_price": high_level,
                    "direction": "Above",
                    "breach_type": breach_type,
                    "interpretation": interpretation,
                    "candle_close": row["Close"],
                    "time": idx.strftime("%Y-%m-%d %H:%M"),
                })

            # Breach below low level
            if row["Low"] <= low_level:
                breach_type = "Close" if row["Close"] <= low_level else "Wick"
                interpretation = _classify_breach("below", breach_type, row, low_level)
                breaches.append({
                    "level": f"{level_name} Low",
                    "level_price": low_level,
                    "direction": "Below",
                    "breach_type": breach_type,
                    "interpretation": interpretation,
                    "candle_close": row["Close"],
                    "time": idx.strftime("%Y-%m-%d %H:%M"),
                })

    # Deduplicate: keep most recent breach per level
    seen = {}
    for b in breaches:
        key = b["level"]
        if key not in seen or b["time"] > seen[key]["time"]:
            seen[key] = b

    return sorted(seen.values(), key=lambda x: x["time"], reverse=True)


def _classify_breach(direction: str, breach_type: str, row: pd.Series, level_price: float) -> str:
    """Classify a breach into a human-readable interpretation."""
    if direction == "below" and breach_type == "Wick":
        return "Liquidity Sweep"
    elif direction == "above" and breach_type == "Wick":
        return "Liquidity Sweep"
    elif direction == "above" and breach_type == "Close":
        # Closed above — check if it's a strong breakout
        distance = row["Close"] - level_price
        if distance > 0:
            return "Breakout"
        return "Reclaim"
    elif direction == "below" and breach_type == "Close":
        distance = level_price - row["Close"]
        if distance > 0:
            return "Breakout"
        return "Reclaim"
    return "False Break"


def interpret_breaches(breaches: list[dict]) -> dict:
    """
    Summarize breach behavior into a directional bias component.
    Returns {"bias": "bullish"|"bearish"|"neutral", "reason": str}
    """
    if not breaches:
        return {"bias": "neutral", "reason": "No recent breaches detected"}

    bullish = 0
    bearish = 0
    reasons = []

    for b in breaches:
        if b["direction"] == "Below" and b["breach_type"] == "Wick":
            bullish += 1
            reasons.append(f"sweep below {b['level']}")
        elif b["direction"] == "Above" and b["breach_type"] == "Wick":
            bearish += 1
            reasons.append(f"sweep above {b['level']}")
        elif b["direction"] == "Above" and b["breach_type"] == "Close":
            bullish += 1
            reasons.append(f"breakout above {b['level']}")
        elif b["direction"] == "Below" and b["breach_type"] == "Close":
            bearish += 1
            reasons.append(f"breakdown below {b['level']}")

    if bullish > bearish:
        return {"bias": "bullish", "reason": "; ".join(reasons[:3])}
    elif bearish > bullish:
        return {"bias": "bearish", "reason": "; ".join(reasons[:3])}
    return {"bias": "neutral", "reason": "mixed breach signals"}


def detect_liquidity_sweeps(
    df: pd.DataFrame, session_levels: dict, key_levels: dict, lookback_bars: int = 12
) -> list[dict]:
    """
    Detect liquidity sweep events: price wicks beyond a key level then closes back.

    Checks session levels and previous day/week levels.
    Returns list of sweep event dicts.
    """
    if len(df) < 2:
        return []

    recent = df.iloc[-lookback_bars:]
    sweeps = []

    # Build a flat list of levels to check
    check_levels = {}
    for name, vals in session_levels.items():
        check_levels[f"{name} High"] = vals["high"]
        check_levels[f"{name} Low"] = vals["low"]

    for name in ["Previous Day", "Current Day"]:
        if name in key_levels:
            check_levels[f"{name} High"] = key_levels[name]["high"]
            check_levels[f"{name} Low"] = key_levels[name]["low"]

    for level_name, level_price in check_levels.items():
        is_high = level_name.endswith("High")

        for idx, row in recent.iterrows():
            if is_high:
                # Wick above high then close below = sweep
                if row["High"] > level_price and row["Close"] < level_price:
                    sweeps.append({
                        "event": f"{level_name} Sweep",
                        "level_price": level_price,
                        "direction": "Bearish",
                        "detail": f"Wicked above {level_price:.5f}, closed back below",
                        "time": idx.strftime("%Y-%m-%d %H:%M"),
                    })
            else:
                # Wick below low then close above = sweep
                if row["Low"] < level_price and row["Close"] > level_price:
                    sweeps.append({
                        "event": f"{level_name} Sweep",
                        "level_price": level_price,
                        "direction": "Bullish",
                        "detail": f"Wicked below {level_price:.5f}, closed back above",
                        "time": idx.strftime("%Y-%m-%d %H:%M"),
                    })

    # Deduplicate: keep most recent per event name
    seen = {}
    for s in sweeps:
        key = s["event"]
        if key not in seen or s["time"] > seen[key]["time"]:
            seen[key] = s

    return sorted(seen.values(), key=lambda x: x["time"], reverse=True)
