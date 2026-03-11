"""
Signal engine: deterministic rule-based directional bias generator.

Combines trend, momentum, level positioning, breach behavior, and news risk
into a weighted score that produces LONG, SHORT, or STAY OUT.
"""

from config import (
    WEIGHTS, RSI_BULLISH, RSI_BEARISH,
    SIGNAL_LONG_THRESHOLD, SIGNAL_SHORT_THRESHOLD,
)


def assess_trend(indicators: dict, daily_indicators: dict | None = None) -> dict:
    """
    Step 1: Higher timeframe trend.

    Bullish if price > EMA 200, bearish if below, neutral if EMA 200 unavailable.
    Uses daily indicators if available, falls back to hourly.
    """
    source = daily_indicators if daily_indicators else indicators
    price = source.get("current_price")
    ema200 = source.get("ema_200")

    if price is None or ema200 is None:
        return {"score": 0.0, "label": "neutral", "reason": "EMA 200 data unavailable"}

    # Also check EMA 50 for additional confirmation
    ema50 = source.get("ema_50")

    if price > ema200:
        if ema50 and price > ema50:
            return {"score": 1.0, "label": "bullish", "reason": "price above EMA 200 and EMA 50"}
        return {"score": 0.6, "label": "bullish", "reason": "price above EMA 200"}
    elif price < ema200:
        if ema50 and price < ema50:
            return {"score": -1.0, "label": "bearish", "reason": "price below EMA 200 and EMA 50"}
        return {"score": -0.6, "label": "bearish", "reason": "price below EMA 200"}
    else:
        return {"score": 0.0, "label": "neutral", "reason": "price at EMA 200"}


def assess_momentum(indicators: dict) -> dict:
    """
    Step 2: Momentum assessment using RSI and MACD.
    """
    rsi = indicators.get("rsi")
    macd_hist = indicators.get("macd_histogram")

    if rsi is None:
        return {"score": 0.0, "label": "neutral", "reason": "RSI unavailable"}

    rsi_bull = rsi > RSI_BULLISH
    rsi_bear = rsi < RSI_BEARISH
    macd_bull = macd_hist is not None and macd_hist > 0
    macd_bear = macd_hist is not None and macd_hist < 0

    if rsi_bull and macd_bull:
        return {"score": 1.0, "label": "bullish",
                "reason": f"RSI {rsi:.1f} > {RSI_BULLISH} and MACD histogram positive"}
    elif rsi_bear and macd_bear:
        return {"score": -1.0, "label": "bearish",
                "reason": f"RSI {rsi:.1f} < {RSI_BEARISH} and MACD histogram negative"}
    elif rsi_bull:
        return {"score": 0.4, "label": "leaning bullish",
                "reason": f"RSI {rsi:.1f} > {RSI_BULLISH} but MACD not confirming"}
    elif rsi_bear:
        return {"score": -0.4, "label": "leaning bearish",
                "reason": f"RSI {rsi:.1f} < {RSI_BEARISH} but MACD not confirming"}
    else:
        return {"score": 0.0, "label": "neutral",
                "reason": f"RSI {rsi:.1f} is neutral range"}


def assess_levels(indicators: dict, levels: dict) -> dict:
    """
    Step 3: Price location relative to key levels.

    Checks if price is above/below important prior highs and lows.
    """
    price = indicators.get("current_price")
    if price is None or not levels:
        return {"score": 0.0, "label": "neutral", "reason": "insufficient level data"}

    above_count = 0
    below_count = 0
    total = 0

    for level_name in ["Previous Day", "Previous Week"]:
        if level_name in levels:
            total += 1
            mid = (levels[level_name]["high"] + levels[level_name]["low"]) / 2
            if price > mid:
                above_count += 1
            else:
                below_count += 1

    if total == 0:
        return {"score": 0.0, "label": "neutral", "reason": "no reference levels available"}

    if above_count > below_count:
        return {"score": 0.8, "label": "bullish",
                "reason": f"price above {above_count}/{total} key level midpoints"}
    elif below_count > above_count:
        return {"score": -0.8, "label": "bearish",
                "reason": f"price below {below_count}/{total} key level midpoints"}
    else:
        return {"score": 0.0, "label": "neutral",
                "reason": "price between key levels"}


def assess_breach(breach_interpretation: dict) -> dict:
    """
    Step 4: Breach behavior interpretation.
    """
    bias = breach_interpretation.get("bias", "neutral")
    reason = breach_interpretation.get("reason", "no breach data")

    if bias == "bullish":
        return {"score": 0.8, "label": "bullish", "reason": reason}
    elif bias == "bearish":
        return {"score": -0.8, "label": "bearish", "reason": reason}
    else:
        return {"score": 0.0, "label": "neutral", "reason": reason}


def assess_news(news_blocking: bool, news_desc: str) -> dict:
    """
    Step 5: News risk filter.

    If high-impact news is imminent, push toward STAY OUT.
    """
    if news_blocking:
        return {"score": 0.0, "label": "blocking",
                "reason": f"high-impact event approaching: {news_desc}"}
    else:
        return {"score": 0.0, "label": "clear",
                "reason": "no imminent high-impact news"}


def generate_signal(
    indicators: dict,
    daily_indicators: dict | None,
    levels: dict,
    breach_interpretation: dict,
    news_blocking: bool,
    news_desc: str,
) -> dict:
    """
    Step 6: Combine all components into a final signal.

    Returns:
        {
            "signal": "LONG" | "SHORT" | "STAY OUT",
            "confidence": float (0-100),
            "regime": str,
            "components": dict of component assessments,
            "explanation": str,
        }
    """
    trend = assess_trend(indicators, daily_indicators)
    momentum = assess_momentum(indicators)
    level_pos = assess_levels(indicators, levels)
    breach = assess_breach(breach_interpretation)
    news = assess_news(news_blocking, news_desc)

    components = {
        "trend": trend,
        "momentum": momentum,
        "levels": level_pos,
        "breach": breach,
        "news": news,
    }

    # Weighted score
    raw_score = (
        WEIGHTS["trend"] * trend["score"] +
        WEIGHTS["momentum"] * momentum["score"] +
        WEIGHTS["levels"] * level_pos["score"] +
        WEIGHTS["breach"] * breach["score"]
    )

    # News override: if blocking, dampen the score significantly
    if news_blocking:
        raw_score *= 0.3

    # Determine signal
    if news_blocking:
        signal = "STAY OUT"
        reason_prefix = "STAY OUT"
    elif raw_score >= SIGNAL_LONG_THRESHOLD:
        signal = "LONG"
        reason_prefix = "LONG"
    elif raw_score <= SIGNAL_SHORT_THRESHOLD:
        signal = "SHORT"
        reason_prefix = "SHORT"
    else:
        signal = "STAY OUT"
        reason_prefix = "STAY OUT"

    # Confidence: how strong the signal is (0-100)
    confidence = min(abs(raw_score) * 100, 100)

    # Determine market regime
    if trend["label"] in ("bullish",):
        regime = "Bullish Trend"
    elif trend["label"] in ("bearish",):
        regime = "Bearish Trend"
    else:
        regime = "Ranging / Mixed"

    # Build explanation
    explanation_parts = [f"{reason_prefix} because:"]
    explanation_parts.append(f"  - Trend: {trend['label']} ({trend['reason']})")
    explanation_parts.append(f"  - Momentum: {momentum['label']} ({momentum['reason']})")
    explanation_parts.append(f"  - Levels: {level_pos['label']} ({level_pos['reason']})")
    explanation_parts.append(f"  - Breaches: {breach['label']} ({breach['reason']})")
    explanation_parts.append(f"  - News: {news['label']} ({news['reason']})")
    explanation = "\n".join(explanation_parts)

    return {
        "signal": signal,
        "confidence": round(confidence, 1),
        "regime": regime,
        "raw_score": round(raw_score, 4),
        "components": components,
        "explanation": explanation,
    }
