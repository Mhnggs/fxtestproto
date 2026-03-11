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
    """Step 1: Higher timeframe trend using EMA 200 and EMA 50."""
    source = daily_indicators if daily_indicators else indicators
    price = source.get("current_price")
    ema200 = source.get("ema_200")

    if price is None or ema200 is None:
        return {"score": 0.0, "label": "neutral", "reason": "EMA 200 data unavailable"}

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
    """Step 2: Momentum from RSI and MACD."""
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
                "reason": f"RSI {rsi:.1f} > {RSI_BULLISH}, MACD histogram positive"}
    elif rsi_bear and macd_bear:
        return {"score": -1.0, "label": "bearish",
                "reason": f"RSI {rsi:.1f} < {RSI_BEARISH}, MACD histogram negative"}
    elif rsi_bull:
        return {"score": 0.4, "label": "leaning bullish",
                "reason": f"RSI {rsi:.1f} > {RSI_BULLISH}, MACD not confirming"}
    elif rsi_bear:
        return {"score": -0.4, "label": "leaning bearish",
                "reason": f"RSI {rsi:.1f} < {RSI_BEARISH}, MACD not confirming"}
    else:
        return {"score": 0.0, "label": "neutral",
                "reason": f"RSI {rsi:.1f} in neutral range"}


def assess_levels(indicators: dict, levels: dict) -> dict:
    """Step 3: Price positioning relative to key level midpoints."""
    price = indicators.get("current_price")
    if price is None or not levels:
        return {"score": 0.0, "label": "neutral", "reason": "insufficient level data"}

    above = 0
    below = 0
    total = 0

    for level_name in ["Previous Day", "Previous Week"]:
        if level_name in levels:
            total += 1
            mid = (levels[level_name]["high"] + levels[level_name]["low"]) / 2
            if price > mid:
                above += 1
            else:
                below += 1

    if total == 0:
        return {"score": 0.0, "label": "neutral", "reason": "no reference levels available"}

    if above > below:
        return {"score": 0.8, "label": "bullish",
                "reason": f"price above {above}/{total} key level midpoints"}
    elif below > above:
        return {"score": -0.8, "label": "bearish",
                "reason": f"price below {below}/{total} key level midpoints"}
    return {"score": 0.0, "label": "neutral", "reason": "price between key levels"}


def assess_breach(breach_interpretation: dict) -> dict:
    """Step 4: Breach behavior interpretation."""
    bias = breach_interpretation.get("bias", "neutral")
    reason = breach_interpretation.get("reason", "no breach data")

    score_map = {"bullish": 0.8, "bearish": -0.8, "neutral": 0.0}
    return {"score": score_map.get(bias, 0.0), "label": bias, "reason": reason}


def assess_news(news_blocking: bool, news_desc: str) -> dict:
    """Step 5: News risk filter."""
    if news_blocking:
        return {"score": 0.0, "label": "blocking",
                "reason": f"high-impact event approaching: {news_desc}"}
    return {"score": 0.0, "label": "clear", "reason": "no imminent high-impact news"}


def _determine_regime(trend: dict, indicators: dict) -> str:
    """Determine market regime label."""
    atr = indicators.get("atr")
    ema20 = indicators.get("ema_20")
    ema50 = indicators.get("ema_50")
    price = indicators.get("current_price")

    # Check volatility
    high_vol = False
    if atr and price:
        atr_pct = atr / price
        high_vol = atr_pct > 0.008  # >0.8% of price = high vol

    if high_vol:
        return "High Volatility"

    if trend["label"] == "bullish":
        return "Bullish Trend"
    elif trend["label"] == "bearish":
        return "Bearish Trend"

    # Check for range: EMAs close together
    if ema20 and ema50 and price:
        ema_spread = abs(ema20 - ema50) / price
        if ema_spread < 0.002:
            return "Range"

    return "Ranging / Mixed"


def generate_signal(
    indicators: dict,
    daily_indicators: dict | None,
    levels: dict,
    breach_interpretation: dict,
    news_blocking: bool,
    news_desc: str,
) -> dict:
    """
    Combine all components into a final signal with score breakdown.

    Returns dict with signal, confidence, regime, raw_score, components,
    score_breakdown, and explanation.
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

    # Weighted scores
    trend_weighted = WEIGHTS["trend"] * trend["score"]
    momentum_weighted = WEIGHTS["momentum"] * momentum["score"]
    levels_weighted = WEIGHTS["levels"] * level_pos["score"]
    breach_weighted = WEIGHTS["breach"] * breach["score"]
    news_weighted = 0.0  # News is a filter, not a score contributor

    raw_score = trend_weighted + momentum_weighted + levels_weighted + breach_weighted

    # Score breakdown for transparency
    score_breakdown = {
        "Trend Score": round(trend_weighted, 3),
        "Momentum Score": round(momentum_weighted, 3),
        "Structure Score": round(levels_weighted, 3),
        "Breach Score": round(breach_weighted, 3),
        "News Risk Score": round(news_weighted, 3),
        "Final Score": round(raw_score, 3),
    }

    # News override
    if news_blocking:
        raw_score *= 0.3

    # Determine signal
    if news_blocking:
        signal = "STAY OUT"
    elif raw_score >= SIGNAL_LONG_THRESHOLD:
        signal = "LONG"
    elif raw_score <= SIGNAL_SHORT_THRESHOLD:
        signal = "SHORT"
    else:
        signal = "STAY OUT"

    confidence = min(abs(raw_score) * 100, 100)
    regime = _determine_regime(trend, indicators)

    # Build explanation
    parts = [f"{signal} because:"]
    parts.append(f"  Trend: {trend['label']} ({trend['reason']})")
    parts.append(f"  Momentum: {momentum['label']} ({momentum['reason']})")
    parts.append(f"  Structure: {level_pos['label']} ({level_pos['reason']})")
    parts.append(f"  Breaches: {breach['label']} ({breach['reason']})")
    parts.append(f"  News: {news['label']} ({news['reason']})")

    return {
        "signal": signal,
        "confidence": round(confidence, 1),
        "regime": regime,
        "raw_score": round(raw_score, 4),
        "components": components,
        "score_breakdown": score_breakdown,
        "explanation": "\n".join(parts),
    }
