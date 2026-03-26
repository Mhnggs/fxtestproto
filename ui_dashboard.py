"""
FX Trading Dashboard — Premium Streamlit UI
Directional bias engine: LONG / SHORT / STAY OUT
"""

import datetime as dt
import streamlit as st
import pandas as pd

from config import PAIRS, SESSIONS, PIP_MULTIPLIER
from styles import THEME_CSS
from data_fetcher import fetch_candle_data, fetch_daily_data
from indicator_engine import compute_all_indicators, get_indicator_summary
from level_engine import compute_key_levels, build_level_rows
from session_engine import compute_all_session_levels
from breach_detector import detect_breaches, interpret_breaches, detect_liquidity_sweeps
from signal_engine import generate_signal
from news_engine import fetch_news, has_high_impact_news_soon, get_news_risk_status
from chart import build_chart


# ─────────────────────────────────────────
# Page setup
# ─────────────────────────────────────────
st.set_page_config(page_title="FX Trading Dashboard", page_icon="📊", layout="wide")
st.markdown(THEME_CSS, unsafe_allow_html=True)


# ─────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────
def _fmt(price: float, pair: str) -> str:
    return f"{price:.2f}" if price > 50 else f"{price:.5f}"


def _sig_cls(signal: str) -> str:
    return {"LONG": "sig-long", "SHORT": "sig-short"}.get(signal, "sig-stay")


def _gauge_color(signal: str) -> str:
    return {"LONG": "#22c55e", "SHORT": "#ef4444"}.get(signal, "#f59e0b")


def _score_cls(v: float) -> str:
    if v > 0.001:
        return "score-pos"
    if v < -0.001:
        return "score-neg"
    return "score-zero"


def _score_fmt(v: float) -> str:
    return f"+{v:.3f}" if v >= 0 else f"{v:.3f}"


def _interp_tag_cls(interp: str) -> str:
    return {
        "Breakout": "tag-breakout",
        "Liquidity Sweep": "tag-sweep",
        "Reclaim": "tag-reclaim",
    }.get(interp, "tag-falsebreak")


def _status_cls(status: str) -> str:
    return {
        "untouched": "status-untouched",
        "breached": "status-breached",
        "reclaimed": "status-reclaimed",
        "active resistance": "status-resistance",
        "active support": "status-support",
    }.get(status, "status-untouched")


def _alert_style(interp: str, direction: str) -> str:
    """Return inline CSS style for alert card based on interpretation."""
    if interp in ("Liquidity Sweep", "False Break"):
        return ("background:rgba(245,158,11,0.06); border:1px solid rgba(245,158,11,0.2); "
                "border-left:3px solid #f59e0b;")
    if direction == "Above" and interp == "Breakout":
        return ("background:rgba(34,197,94,0.06); border:1px solid rgba(34,197,94,0.2); "
                "border-left:3px solid #22c55e;")
    if direction == "Below" and interp == "Breakout":
        return ("background:rgba(239,68,68,0.06); border:1px solid rgba(239,68,68,0.2); "
                "border-left:3px solid #ef4444;")
    if interp == "Reclaim":
        if direction == "Below":
            return ("background:rgba(34,197,94,0.06); border:1px solid rgba(34,197,94,0.2); "
                    "border-left:3px solid #22c55e;")
        return ("background:rgba(239,68,68,0.06); border:1px solid rgba(239,68,68,0.2); "
                "border-left:3px solid #ef4444;")
    return ("background:rgba(245,158,11,0.06); border:1px solid rgba(245,158,11,0.2); "
            "border-left:3px solid #f59e0b;")


# ─────────────────────────────────────────
# Render functions
# ─────────────────────────────────────────
def render_top_bar():
    """Premium top bar with selectors."""
    c1, c2, c3, c4, c5 = st.columns([2.2, 0.8, 0.8, 0.5, 1.7])

    with c1:
        st.markdown(
            '<div class="top-bar-title">FX Trading Dashboard</div>'
            '<div class="top-bar-subtitle">Directional Bias Engine</div>',
            unsafe_allow_html=True,
        )

    with c2:
        pair = st.selectbox("Pair", list(PAIRS.keys()), key="pair_select", label_visibility="collapsed")

    with c3:
        session = st.selectbox("Session", list(SESSIONS.keys()), key="session_select", label_visibility="collapsed")

    with c4:
        st.write("")
        st.button("⟳", key="refresh", use_container_width=True)

    with c5:
        st.write("")
        ts = dt.datetime.utcnow().strftime("%Y-%m-%d  %H:%M UTC")
        st.markdown(f'<div class="top-bar-ts" style="text-align:right; padding-top:0.3rem;">{ts}</div>',
                    unsafe_allow_html=True)

    return pair, session


def render_alert_bar(breaches: list[dict]):
    """Prominent alert bar for recent level breaches."""
    important = breaches[:5]
    if not important:
        return

    cards = ""
    for b in important:
        card_style = _alert_style(b.get("interpretation", ""), b["direction"])
        interp = b.get("interpretation", b["breach_type"])
        cards += (
            f'<div style="flex:0 0 auto; min-width:280px; max-width:320px; border-radius:8px; '
            f'padding:0.65rem 0.9rem; font-size:0.8rem; line-height:1.4; {card_style}">'
            f'<div style="font-weight:600; color:#e2e8f0;">{b["level"]}</div>'
            f'<div style="color:#94a3b8; font-size:0.75rem;">{interp} — {b["breach_type"]} {b["direction"].lower()}</div>'
            f'<div style="font-family:JetBrains Mono,monospace; font-size:0.68rem; color:#64748b;">{b["time"]} UTC</div>'
            f'</div>'
        )

    st.markdown(
        f'<div style="display:flex; flex-direction:row; flex-wrap:nowrap; gap:0.5rem; '
        f'overflow-x:auto; padding:0.4rem 0; margin-bottom:0.8rem;">{cards}</div>',
        unsafe_allow_html=True,
    )


def render_summary(price_str: str, result: dict):
    """Four premium summary cards."""
    signal = result["signal"]
    confidence = result["confidence"]
    regime = result["regime"]
    gc = _gauge_color(signal)
    sc = _sig_cls(signal)

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(f"""
        <div class="summary-card">
            <div class="summary-label">Current Price</div>
            <div class="summary-value">{price_str}</div>
        </div>""", unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="summary-card">
            <div class="summary-label">Signal</div>
            <div class="summary-value {sc}">{signal}</div>
        </div>""", unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="summary-card">
            <div class="summary-label">Confidence</div>
            <div class="summary-value">{confidence:.0f}<span style="font-size:1rem; color:#64748b;">%</span></div>
            <div class="gauge-track">
                <div class="gauge-bar" style="width:{min(confidence,100)}%; background:{gc};"></div>
            </div>
        </div>""", unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
        <div class="summary-card">
            <div class="summary-label">Market Regime</div>
            <div class="summary-value summary-value-sm">{regime}</div>
        </div>""", unsafe_allow_html=True)


def render_explanation(result: dict):
    """Premium signal explanation panel."""
    st.markdown('<div class="sec-header">Signal Explanation</div>', unsafe_allow_html=True)

    signal = result["signal"]
    sc = _sig_cls(signal)
    components = result["components"]

    comp_labels = {
        "trend": "Trend", "momentum": "Momentum",
        "levels": "Structure", "breach": "Breaches", "news": "News",
    }

    lines = []
    for comp_name in ["trend", "momentum", "levels", "breach", "news"]:
        comp = components[comp_name]
        label = comp_labels[comp_name]
        lines.append(
            f'<div style="padding:0.15rem 0 0.15rem 0.6rem; margin:0.1rem 0; '
            f'border-left:2px solid rgba(148,163,184,0.1); font-size:0.78rem; line-height:1.5;">'
            f'<span style="color:#64748b;">{label}:</span> '
            f'<span style="color:#cbd5e1;">{comp["label"]}</span> '
            f'<span style="color:#475569;">&mdash; {comp["reason"]}</span>'
            f'</div>'
        )

    reasons_block = "\n".join(lines)
    html = (
        f'<div style="background:linear-gradient(135deg,#0c1222,#0f172a); '
        f'border:1px solid rgba(56,189,248,0.1); border-left:3px solid #38bdf8; '
        f'padding:1rem 1.2rem; border-radius:8px;">'
        f'<div class="{sc}" style="font-weight:700; font-size:0.9rem; '
        f'font-family:JetBrains Mono,monospace; margin-bottom:0.5rem;">{signal}</div>'
        f'{reasons_block}'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def render_score_breakdown(breakdown: dict):
    """Transparent score breakdown with mini bars."""
    st.markdown('<div class="sec-header">Score Breakdown</div>', unsafe_allow_html=True)

    rows = ""
    for label, val in breakdown.items():
        is_final = label == "Final Score"
        cls = _score_cls(val)
        row_cls = "score-row score-row-final" if is_final else "score-row"

        # Bar width: scale absolute value, max 50% of track (one side)
        bar_pct = min(abs(val) / 0.5 * 50, 50)
        bar_cls = "score-bar-fill score-bar-fill-pos" if val >= 0 else "score-bar-fill score-bar-fill-neg"
        bar_style = f"width:{bar_pct}%;"

        name_style = "font-weight:700; color:#e2e8f0;" if is_final else ""
        val_style = "font-weight:700;" if is_final else ""

        rows += f"""
        <div class="{row_cls}">
            <span class="score-name" style="{name_style}">{label}</span>
            <div class="score-bar-track"><div class="{bar_cls}" style="{bar_style}"></div></div>
            <span class="score-val {cls}" style="{val_style}">{_score_fmt(val)}</span>
        </div>"""

    st.markdown(f'<div class="panel">{rows}</div>', unsafe_allow_html=True)


def render_indicators(indicators: dict):
    """Indicator readings panel."""
    st.markdown('<div class="sec-header">Indicators</div>', unsafe_allow_html=True)

    summary = get_indicator_summary(indicators)
    rows = ""
    for item in summary:
        rows += f"""
        <div class="ind-row">
            <span class="ind-name">{item['Indicator']}</span>
            <span class="ind-val">{item['Value']}</span>
        </div>"""

    st.markdown(f'<div class="panel">{rows}</div>', unsafe_allow_html=True)


def render_market_regime(result: dict, indicators: dict, session_levels: dict, pair: str):
    """Market conditions panel."""
    st.markdown('<div class="sec-header">Market Conditions</div>', unsafe_allow_html=True)

    atr = indicators.get("atr")
    price = indicators.get("current_price", 1.0)

    vol = "Normal"
    if atr and price:
        pct = (atr / price) * 100
        if pct > 0.8:
            vol = "High"
        elif pct < 0.3:
            vol = "Low"

    total_range = sum(v["high"] - v["low"] for v in session_levels.values())
    avg_range = total_range / max(len(session_levels), 1)
    range_pct = (avg_range / atr * 100) if atr and atr > 0 else 0

    trend = result["components"]["trend"]["label"].title()
    regime = result["regime"]

    items = [
        ("Trend", trend),
        ("Volatility", vol),
        ("Session Range", f"{range_pct:.0f}% of ATR"),
        ("Market State", regime),
    ]

    rows = ""
    for label, val in items:
        rows += f"""
        <div class="regime-row">
            <span class="regime-label">{label}</span>
            <span class="regime-val">{val}</span>
        </div>"""

    st.markdown(f'<div class="panel">{rows}</div>', unsafe_allow_html=True)


def render_news(pair: str):
    """News and event risk panel."""
    st.markdown('<div class="sec-header">News &amp; Event Risk</div>', unsafe_allow_html=True)

    risk = get_news_risk_status(pair)
    badge_cls = {"Clear": "badge-clear", "Caution": "badge-caution", "Block": "badge-block"}.get(
        risk["status"], "badge-clear")

    st.markdown(f"""
    <div class="panel">
        <div class="regime-row">
            <span class="regime-label">Next Event</span>
            <span class="regime-val" style="font-size:0.82rem;">{risk['next_event']}</span>
        </div>
        <div class="regime-row">
            <span class="regime-label">Time Until</span>
            <span style="font-family:'JetBrains Mono',monospace; color:#e2e8f0; font-size:0.82rem;">{risk['time_until']}</span>
        </div>
        <div class="regime-row">
            <span class="regime-label">Risk Status</span>
            <span class="news-risk-badge {badge_cls}">{risk['status']}</span>
        </div>
    </div>""", unsafe_allow_html=True)

    news_items = fetch_news(pair)
    for item in news_items:
        icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(item["impact"], "⚪")
        st.markdown(f"""
        <div class="news-item">
            <div class="news-headline">{icon} {item['headline']}</div>
            <div class="news-meta">{item['source']} · {item['timestamp']}</div>
        </div>""", unsafe_allow_html=True)


def render_sweeps(sweeps: list[dict]):
    """Liquidity events panel."""
    st.markdown('<div class="sec-header">Liquidity Events</div>', unsafe_allow_html=True)

    if not sweeps:
        st.markdown(
            '<div class="panel" style="color:#334155; text-align:center; font-size:0.82rem;">No sweeps detected</div>',
            unsafe_allow_html=True)
        return

    for s in sweeps:
        dc = "#22c55e" if s["direction"] == "Bullish" else "#ef4444"
        st.markdown(f"""
        <div class="sweep-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span class="sweep-name">{s['event']}</span>
                <span class="sweep-time">{s['time']}</span>
            </div>
            <div class="sweep-detail">{s['detail']}</div>
            <div style="color:{dc}; font-size:0.72rem; font-weight:600; margin-top:0.15rem;">{s['direction']}</div>
        </div>""", unsafe_allow_html=True)


def render_key_levels(level_rows: list[dict], pair: str):
    """Premium key levels panel with status."""
    st.markdown('<div class="sec-header">Key Levels</div>', unsafe_allow_html=True)

    if not level_rows:
        st.markdown('<div class="panel" style="color:#334155; text-align:center;">No data</div>',
                    unsafe_allow_html=True)
        return

    dec = 2 if level_rows[0]["price"] > 50 else 5

    rows = ""
    for r in level_rows:
        st_cls = _status_cls(r["status"])
        dist = r["distance_pips"]
        dist_cls = "score-pos" if dist > 0 else "score-neg" if dist < 0 else "score-zero"
        dist_str = f"+{dist}" if dist > 0 else str(dist)

        rows += f"""
        <div class="level-row">
            <span class="level-name">{r['level']}</span>
            <span class="level-price">{r['price']:.{dec}f}</span>
            <span class="level-dist {dist_cls}">{dist_str}p</span>
            <span class="level-status {st_cls}">{r['status']}</span>
        </div>"""

    st.markdown(f'<div class="panel" style="max-height:420px; overflow-y:auto;">{rows}</div>',
                unsafe_allow_html=True)


def render_session_levels(session_levels: dict, current_price: float, pair: str):
    """Session levels cards."""
    st.markdown('<div class="sec-header">Session Levels</div>', unsafe_allow_html=True)

    if not session_levels:
        st.markdown('<div class="panel" style="color:#334155; text-align:center;">No data</div>',
                    unsafe_allow_html=True)
        return

    pip_mult = PIP_MULTIPLIER.get(pair, 10000)
    dec = 2 if current_price > 50 else 5
    sess_colors = {"Asia": "#f59e0b", "London": "#3b82f6", "New York": "#22c55e"}

    for name, vals in session_levels.items():
        color = sess_colors.get(name, "#64748b")
        dist_h = round((vals["high"] - current_price) * pip_mult, 1)
        dist_l = round((vals["low"] - current_price) * pip_mult, 1)

        st.markdown(f"""
        <div class="session-card" style="border-left: 3px solid {color};">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span class="session-name" style="color:{color};">{name}</span>
                <span class="session-range">Range: {vals['range_pips']} pips</span>
            </div>
            <div class="session-vals">
                <span style="color:#94a3b8;">H <span style="color:#e2e8f0;">{vals['high']:.{dec}f}</span>
                    <span style="color:#475569; font-size:0.7rem;">({dist_h:+.1f}p)</span></span>
                <span style="color:#94a3b8;">L <span style="color:#e2e8f0;">{vals['low']:.{dec}f}</span>
                    <span style="color:#475569; font-size:0.7rem;">({dist_l:+.1f}p)</span></span>
            </div>
        </div>""", unsafe_allow_html=True)


def render_breach_log(breaches: list[dict], pair: str):
    """Breach analysis event log."""
    st.markdown('<div class="sec-header">Breach Analysis</div>', unsafe_allow_html=True)

    if not breaches:
        st.markdown(
            '<div class="panel" style="color:#334155; text-align:center; font-size:0.82rem;">No breaches</div>',
            unsafe_allow_html=True)
        return

    dec = 5
    if breaches and breaches[0].get("level_price", 0) > 50:
        dec = 2

    rows = ""
    for b in breaches:
        interp = b.get("interpretation", b["breach_type"])
        tag_cls = _interp_tag_cls(interp)
        rows += f"""
        <div class="breach-row">
            <span class="breach-time">{b['time']}</span>
            <span class="breach-level">{b['level']}</span>
            <span class="breach-tag {tag_cls}">{interp}</span>
        </div>"""

    st.markdown(f'<div class="panel" style="max-height:380px; overflow-y:auto;">{rows}</div>',
                unsafe_allow_html=True)


def render_debug(indicators: dict, result: dict, breaches: list[dict]):
    """Debug panel with raw analysis data."""
    st.markdown('<div class="sec-header">Debug Output</div>', unsafe_allow_html=True)

    components = result["components"]
    text = "INDICATORS\n"
    for k in ["current_price", "ema_20", "ema_50", "ema_200", "rsi",
              "macd_line", "macd_signal", "macd_histogram", "atr"]:
        v = indicators.get(k)
        if v is not None:
            text += f"  {k}: {v}\n"

    text += "\nCOMPONENT SCORES\n"
    for name, data in components.items():
        text += f"  {name}: {data['score']:+.3f}  ({data['label']})\n"
        text += f"    → {data['reason']}\n"

    text += f"\nFINAL\n  score: {result['raw_score']}\n  signal: {result['signal']}\n  confidence: {result['confidence']}%\n"

    text += f"\nBREACHES ({len(breaches)})\n"
    for b in breaches[:6]:
        text += f"  [{b['time']}] {b['level']} {b['direction']} ({b['breach_type']}) → {b.get('interpretation', '?')}\n"

    st.markdown(f'<div class="debug-panel"><pre>{text}</pre></div>', unsafe_allow_html=True)


# ─────────────────────────────────────────
# Main
# ─────────────────────────────────────────
def main():
    pair, session = render_top_bar()

    # Fetch data
    with st.spinner("Loading market data..."):
        df_hourly = fetch_candle_data(pair)
        df_daily = fetch_daily_data(pair)

    if df_hourly.empty:
        st.error("Unable to load market data. Check your connection and try again.")
        return

    # Compute
    indicators = compute_all_indicators(df_hourly)
    daily_indicators = compute_all_indicators(df_daily) if not df_daily.empty else None
    levels = compute_key_levels(df_hourly, session)
    session_levels = compute_all_session_levels(df_hourly, pair)
    breaches = detect_breaches(df_hourly, levels)
    breach_interp = interpret_breaches(breaches)
    sweeps = detect_liquidity_sweeps(df_hourly, session_levels, levels)
    news_blocking, news_desc = has_high_impact_news_soon(pair)

    result = generate_signal(
        indicators=indicators,
        daily_indicators=daily_indicators,
        levels=levels,
        breach_interpretation=breach_interp,
        news_blocking=news_blocking,
        news_desc=news_desc,
    )

    current_price = indicators["current_price"]
    price_str = _fmt(current_price, pair)
    level_rows = build_level_rows(levels, current_price, pair, breaches)

    # ═══════════════════════════════════════
    # ALERT BAR
    # ═══════════════════════════════════════
    render_alert_bar(breaches)

    # ═══════════════════════════════════════
    # SUMMARY CARDS
    # ═══════════════════════════════════════
    render_summary(price_str, result)
    st.markdown("<div style='height:0.6rem;'></div>", unsafe_allow_html=True)

    # ═══════════════════════════════════════
    # CHART + SIDEBAR
    # ═══════════════════════════════════════
    chart_col, side_col = st.columns([2.6, 1])

    with chart_col:
        fig = build_chart(df_hourly, indicators, levels, session_levels, breaches, pair)
        st.plotly_chart(fig, use_container_width=True, key=f"chart_{pair}_{session}")

    with side_col:
        render_explanation(result)
        st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
        render_score_breakdown(result["score_breakdown"])
        st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
        render_indicators(indicators)

    # ═══════════════════════════════════════
    # MID PANELS (3 columns)
    # ═══════════════════════════════════════
    m1, m2, m3 = st.columns(3)
    with m1:
        render_market_regime(result, indicators, session_levels, pair)
    with m2:
        render_news(pair)
    with m3:
        render_sweeps(sweeps)

    # ═══════════════════════════════════════
    # BOTTOM PANELS (3 columns)
    # ═══════════════════════════════════════
    st.markdown("<div style='height:0.4rem;'></div>", unsafe_allow_html=True)
    b1, b2, b3 = st.columns(3)
    with b1:
        render_key_levels(level_rows, pair)
    with b2:
        render_session_levels(session_levels, current_price, pair)
    with b3:
        render_breach_log(breaches, pair)

    # ═══════════════════════════════════════
    # DEBUG
    # ═══════════════════════════════════════
    st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
    with st.expander("Debug Mode"):
        render_debug(indicators, result, breaches)

    # Footer
    st.markdown(
        '<div class="dash-footer">FX Trading Dashboard · Rule-based directional bias · Not financial advice</div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
