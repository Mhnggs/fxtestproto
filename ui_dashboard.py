"""
Forex Trading Dashboard — Professional Streamlit UI
Decision support tool: LONG / SHORT / STAY OUT
"""

import datetime as dt
import streamlit as st
import pandas as pd

from config import PAIRS, SESSIONS, PIP_MULTIPLIER
from data_fetcher import fetch_candle_data, fetch_daily_data
from indicator_engine import compute_all_indicators, get_indicator_summary
from level_engine import compute_key_levels, levels_to_dataframe
from session_engine import compute_all_session_levels, session_levels_to_rows
from breach_detector import detect_breaches, interpret_breaches, detect_liquidity_sweeps
from signal_engine import generate_signal
from news_engine import fetch_news, fetch_upcoming_events, has_high_impact_news_soon, get_news_risk_status
from chart import build_chart


# ──────────────────────────────────────────────
# Page config and global styles
# ──────────────────────────────────────────────
st.set_page_config(page_title="FX Dashboard", page_icon="📊", layout="wide")

st.markdown("""
<style>
    /* Dark background */
    .stApp { background-color: #0e1117; }

    /* Card styling */
    .metric-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #2a2a4a;
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .metric-card .label {
        font-size: 0.75rem;
        color: #8892b0;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.3rem;
    }
    .metric-card .value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #e6f1ff;
    }

    /* Signal colors */
    .signal-long { color: #26a69a; }
    .signal-short { color: #ef5350; }
    .signal-stayout { color: #ffa726; }

    /* Section headers */
    .section-header {
        font-size: 1rem;
        font-weight: 600;
        color: #ccd6f6;
        border-bottom: 1px solid #2a2a4a;
        padding-bottom: 0.4rem;
        margin-bottom: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Panel boxes */
    .panel {
        background: #1a1a2e;
        border: 1px solid #2a2a4a;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.5rem;
    }

    /* Explanation */
    .explanation-box {
        background: #0a192f;
        border-left: 3px solid #64ffda;
        padding: 1rem;
        border-radius: 4px;
        font-family: 'SF Mono', 'Fira Code', monospace;
        font-size: 0.85rem;
        white-space: pre-wrap;
        color: #a8b2d1;
        line-height: 1.6;
    }

    /* Score bar */
    .score-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.3rem 0;
        border-bottom: 1px solid #1e1e3f;
        font-size: 0.85rem;
    }
    .score-label { color: #8892b0; }
    .score-pos { color: #26a69a; font-weight: 600; }
    .score-neg { color: #ef5350; font-weight: 600; }
    .score-zero { color: #546e7a; font-weight: 600; }

    /* News risk badges */
    .risk-clear { color: #26a69a; font-weight: 700; }
    .risk-caution { color: #ffa726; font-weight: 700; }
    .risk-block { color: #ef5350; font-weight: 700; }

    /* Regime badge */
    .regime-badge {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 600;
    }

    /* Debug panel */
    .debug-panel {
        background: #0d1117;
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 0.8rem;
        font-family: monospace;
        font-size: 0.78rem;
        color: #8b949e;
    }

    /* Confidence gauge */
    .gauge-container {
        width: 100%;
        height: 8px;
        background: #1e1e3f;
        border-radius: 4px;
        margin-top: 0.5rem;
        overflow: hidden;
    }
    .gauge-fill {
        height: 100%;
        border-radius: 4px;
        transition: width 0.3s;
    }

    /* Sweep event */
    .sweep-event {
        background: #1a1a2e;
        border-left: 3px solid #e040fb;
        padding: 0.5rem 0.8rem;
        margin-bottom: 0.4rem;
        border-radius: 0 4px 4px 0;
        font-size: 0.85rem;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


def _fmt_price(price: float, pair: str) -> str:
    """Format price with appropriate decimals."""
    return f"{price:.2f}" if price > 50 else f"{price:.5f}"


def _signal_class(signal: str) -> str:
    return {"LONG": "signal-long", "SHORT": "signal-short"}.get(signal, "signal-stayout")


def _score_class(val: float) -> str:
    if val > 0:
        return "score-pos"
    elif val < 0:
        return "score-neg"
    return "score-zero"


def _score_sign(val: float) -> str:
    return f"+{val:.3f}" if val >= 0 else f"{val:.3f}"


def _gauge_color(confidence: float, signal: str) -> str:
    if signal == "LONG":
        return "#26a69a"
    elif signal == "SHORT":
        return "#ef5350"
    return "#ffa726"


def render_header():
    """Render top header with pair/session selectors."""
    col_title, col_pair, col_session, col_refresh, col_time = st.columns([2, 1, 1, 0.6, 1.8])

    with col_title:
        st.markdown("## FX Trading Dashboard")
        st.caption("Decision Support Prototype")

    with col_pair:
        pair = st.selectbox("Pair", list(PAIRS.keys()), label_visibility="collapsed")

    with col_session:
        session = st.selectbox("Session", list(SESSIONS.keys()), label_visibility="collapsed")

    with col_refresh:
        st.write("")
        refresh = st.button("⟳ Refresh", use_container_width=True)

    with col_time:
        st.write("")
        st.markdown(
            f"<span style='color:#546e7a; font-size:0.85rem;'>"
            f"Updated: {dt.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}</span>",
            unsafe_allow_html=True,
        )

    return pair, session


def render_summary_cards(price_str: str, result: dict, pair: str):
    """Render the four top summary cards."""
    signal = result["signal"]
    confidence = result["confidence"]
    regime = result["regime"]
    sig_cls = _signal_class(signal)
    gauge_col = _gauge_color(confidence, signal)

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="label">Current Price</div>
            <div class="value">{price_str}</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="label">Signal</div>
            <div class="value {sig_cls}">{signal}</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="label">Confidence</div>
            <div class="value">{confidence:.0f}%</div>
            <div class="gauge-container">
                <div class="gauge-fill" style="width:{min(confidence, 100)}%; background:{gauge_col};"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="label">Market Regime</div>
            <div class="value" style="font-size:1.2rem;">{regime}</div>
        </div>
        """, unsafe_allow_html=True)


def render_score_breakdown(score_breakdown: dict, signal: str):
    """Render transparent score breakdown."""
    st.markdown('<div class="section-header">Score Breakdown</div>', unsafe_allow_html=True)

    html_rows = ""
    for label, val in score_breakdown.items():
        cls = _score_class(val)
        is_final = label == "Final Score"
        weight = "font-weight:700;" if is_final else ""
        border = "border-top: 2px solid #2a2a4a; padding-top: 0.5rem;" if is_final else ""
        html_rows += f"""
        <div class="score-row" style="{border}">
            <span class="score-label" style="{weight}">{label}</span>
            <span class="{cls}" style="{weight}">{_score_sign(val)}</span>
        </div>
        """

    st.markdown(f'<div class="panel">{html_rows}</div>', unsafe_allow_html=True)


def render_market_regime(result: dict, indicators: dict, session_levels: dict, pair: str):
    """Render market regime panel."""
    st.markdown('<div class="section-header">Market Conditions</div>', unsafe_allow_html=True)

    regime = result["regime"]
    atr = indicators.get("atr")
    price = indicators.get("current_price", 1.0)
    pip_mult = PIP_MULTIPLIER.get(pair, 10000)

    # Volatility assessment
    vol_label = "Normal"
    if atr and price:
        atr_pct = (atr / price) * 100
        if atr_pct > 0.8:
            vol_label = "High"
        elif atr_pct < 0.3:
            vol_label = "Low"

    # Session range % of ATR
    total_session_range = 0
    session_count = 0
    for s_name, s_vals in session_levels.items():
        total_session_range += s_vals["high"] - s_vals["low"]
        session_count += 1
    avg_session_range = total_session_range / max(session_count, 1)
    range_pct_atr = (avg_session_range / atr * 100) if atr and atr > 0 else 0

    trend_label = result["components"]["trend"]["label"]

    st.markdown(f"""
    <div class="panel">
        <div style="display:flex; justify-content:space-between; padding:0.2rem 0; color:#a8b2d1;">
            <span>Trend</span><span style="color:#e6f1ff; font-weight:600;">{trend_label.title()}</span>
        </div>
        <div style="display:flex; justify-content:space-between; padding:0.2rem 0; color:#a8b2d1;">
            <span>Volatility</span><span style="color:#e6f1ff; font-weight:600;">{vol_label}</span>
        </div>
        <div style="display:flex; justify-content:space-between; padding:0.2rem 0; color:#a8b2d1;">
            <span>Avg Session Range</span><span style="color:#e6f1ff; font-weight:600;">{range_pct_atr:.0f}% of ATR</span>
        </div>
        <div style="display:flex; justify-content:space-between; padding:0.2rem 0; color:#a8b2d1;">
            <span>Market State</span><span style="color:#e6f1ff; font-weight:600;">{regime}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_news_panel(pair: str):
    """Render news and risk panel."""
    st.markdown('<div class="section-header">News & Event Risk</div>', unsafe_allow_html=True)

    risk = get_news_risk_status(pair)
    risk_cls = {"Clear": "risk-clear", "Caution": "risk-caution", "Block": "risk-block"}.get(
        risk["status"], "risk-clear"
    )

    st.markdown(f"""
    <div class="panel">
        <div style="display:flex; justify-content:space-between; padding:0.3rem 0; color:#a8b2d1;">
            <span>Next Event</span>
            <span style="color:#e6f1ff;">{risk['next_event']}</span>
        </div>
        <div style="display:flex; justify-content:space-between; padding:0.3rem 0; color:#a8b2d1;">
            <span>Time Until</span>
            <span style="color:#e6f1ff;">{risk['time_until']}</span>
        </div>
        <div style="display:flex; justify-content:space-between; padding:0.3rem 0; color:#a8b2d1;">
            <span>Risk Status</span>
            <span class="{risk_cls}">{risk['status']}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    news_items = fetch_news(pair)
    for item in news_items:
        icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(item["impact"], "⚪")
        st.markdown(
            f"<div style='font-size:0.82rem; padding:0.2rem 0; color:#a8b2d1;'>"
            f"{icon} {item['headline']}<br>"
            f"<span style='color:#546e7a; font-size:0.75rem;'>{item['source']} | {item['timestamp']}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )


def render_liquidity_sweeps(sweeps: list[dict]):
    """Render liquidity events panel."""
    st.markdown('<div class="section-header">Liquidity Events</div>', unsafe_allow_html=True)

    if not sweeps:
        st.markdown(
            '<div class="panel" style="color:#546e7a; text-align:center;">No sweeps detected</div>',
            unsafe_allow_html=True,
        )
        return

    for s in sweeps:
        dir_color = "#26a69a" if s["direction"] == "Bullish" else "#ef5350"
        st.markdown(f"""
        <div class="sweep-event">
            <strong style="color:{dir_color};">{s['event']}</strong>
            <span style="color:#546e7a; font-size:0.78rem;"> — {s['time']}</span><br>
            <span style="color:#8892b0; font-size:0.8rem;">{s['detail']}</span>
            <span style="color:{dir_color}; font-size:0.8rem; float:right;">{s['direction']}</span>
        </div>
        """, unsafe_allow_html=True)


def render_debug_panel(indicators: dict, result: dict, breaches: list[dict]):
    """Render optional debug panel with raw values."""
    st.markdown('<div class="section-header">Debug Information</div>', unsafe_allow_html=True)

    components = result["components"]

    debug_text = "=== INDICATOR VALUES ===\n"
    for key in ["current_price", "ema_20", "ema_50", "ema_200", "rsi", "macd_line",
                 "macd_signal", "macd_histogram", "atr"]:
        val = indicators.get(key)
        if val is not None:
            debug_text += f"  {key}: {val}\n"

    debug_text += "\n=== COMPONENT SCORES ===\n"
    for comp_name, comp_data in components.items():
        debug_text += f"  {comp_name}: score={comp_data['score']:.3f} label={comp_data['label']}\n"
        debug_text += f"    reason: {comp_data['reason']}\n"

    debug_text += f"\n=== FINAL ===\n"
    debug_text += f"  raw_score: {result['raw_score']}\n"
    debug_text += f"  signal: {result['signal']}\n"
    debug_text += f"  confidence: {result['confidence']}%\n"

    debug_text += f"\n=== BREACHES ({len(breaches)}) ===\n"
    for b in breaches[:5]:
        debug_text += f"  [{b['time']}] {b['level']} {b['direction']} ({b['breach_type']}) -> {b.get('interpretation', 'N/A')}\n"

    st.markdown(f'<div class="debug-panel"><pre>{debug_text}</pre></div>', unsafe_allow_html=True)


# ──────────────────────────────────────────────
# Main entry point
# ──────────────────────────────────────────────
def main():
    pair, session = render_header()
    st.markdown("<div style='margin-bottom:0.5rem;'></div>", unsafe_allow_html=True)

    # ── Fetch data ──
    with st.spinner("Loading market data..."):
        df_hourly = fetch_candle_data(pair)
        df_daily = fetch_daily_data(pair)

    if df_hourly.empty:
        st.error("No market data available. Please try again.")
        return

    # ── Compute everything ──
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
    price_str = _fmt_price(current_price, pair)
    pip_mult = PIP_MULTIPLIER.get(pair, 10000)
    dec = 2 if current_price > 50 else 5

    # ══════════════════════════════════════════
    # TOP: Summary cards
    # ══════════════════════════════════════════
    render_summary_cards(price_str, result, pair)
    st.markdown("<div style='margin: 0.5rem 0;'></div>", unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # MIDDLE: Chart + Right sidebar
    # ══════════════════════════════════════════
    chart_col, sidebar_col = st.columns([2.5, 1])

    with chart_col:
        fig = build_chart(df_hourly, indicators, levels, session_levels, breaches, pair)
        st.plotly_chart(fig, use_container_width=True)

    with sidebar_col:
        # Signal explanation
        st.markdown('<div class="section-header">Signal Explanation</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="explanation-box">{result["explanation"]}</div>',
            unsafe_allow_html=True,
        )

        st.markdown("<div style='margin:0.8rem 0;'></div>", unsafe_allow_html=True)

        # Score breakdown
        render_score_breakdown(result["score_breakdown"], result["signal"])

        st.markdown("<div style='margin:0.8rem 0;'></div>", unsafe_allow_html=True)

        # Indicator summary
        st.markdown('<div class="section-header">Indicators</div>', unsafe_allow_html=True)
        ind_summary = get_indicator_summary(indicators)
        st.dataframe(
            pd.DataFrame(ind_summary),
            use_container_width=True, hide_index=True, height=320,
        )

    # ══════════════════════════════════════════
    # LOWER MIDDLE: 3-column panels
    # ══════════════════════════════════════════
    st.markdown("<div style='margin: 0.3rem 0;'></div>", unsafe_allow_html=True)
    panel_left, panel_mid, panel_right = st.columns(3)

    with panel_left:
        render_market_regime(result, indicators, session_levels, pair)

    with panel_mid:
        render_news_panel(pair)

    with panel_right:
        render_liquidity_sweeps(sweeps)

    # ══════════════════════════════════════════
    # BOTTOM: Key levels + Session levels + Breaches
    # ══════════════════════════════════════════
    st.markdown("<div style='margin: 0.5rem 0;'></div>", unsafe_allow_html=True)
    bot_left, bot_mid, bot_right = st.columns(3)

    with bot_left:
        st.markdown('<div class="section-header">Key Levels</div>', unsafe_allow_html=True)
        levels_df = levels_to_dataframe(levels, current_price, pair)
        if not levels_df.empty:
            for col in ["High", "Low"]:
                levels_df[col] = levels_df[col].apply(lambda x: f"{x:.{dec}f}")
            st.dataframe(levels_df, use_container_width=True, hide_index=True, height=350)
        else:
            st.info("No level data available.")

    with bot_mid:
        st.markdown('<div class="section-header">Session Levels</div>', unsafe_allow_html=True)
        session_rows = session_levels_to_rows(session_levels, current_price, pair)
        if session_rows:
            sdf = pd.DataFrame(session_rows)
            for col in ["High", "Low"]:
                sdf[col] = sdf[col].apply(lambda x: f"{x:.{dec}f}")
            st.dataframe(sdf, use_container_width=True, hide_index=True, height=350)
        else:
            st.info("No session data available.")

    with bot_right:
        st.markdown('<div class="section-header">Breach Analysis</div>', unsafe_allow_html=True)
        if breaches:
            breach_df = pd.DataFrame(breaches)
            display_cols = ["time", "level", "direction", "breach_type", "interpretation"]
            available = [c for c in display_cols if c in breach_df.columns]
            st.dataframe(breach_df[available], use_container_width=True, hide_index=True, height=350)
        else:
            st.info("No recent breaches detected.")

    # ══════════════════════════════════════════
    # DEBUG MODE (toggle)
    # ══════════════════════════════════════════
    st.markdown("<div style='margin: 0.5rem 0;'></div>", unsafe_allow_html=True)
    debug_on = st.toggle("Debug Mode", value=False)
    if debug_on:
        render_debug_panel(indicators, result, breaches)

    # ── Footer ──
    st.markdown(
        "<div style='text-align:center; color:#546e7a; font-size:0.75rem; "
        "margin-top:1rem; padding:0.5rem; border-top:1px solid #1e1e2f;'>"
        "FX Dashboard Prototype — Rule-based signals, not financial advice. "
        "News data is mocked.</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
