"""
Forex Trading Dashboard - Streamlit Prototype
Decision support tool for directional bias: LONG / SHORT / STAY OUT
"""

import datetime as dt
import streamlit as st
import pandas as pd

from config import PAIRS, SESSIONS
from data_fetcher import (
    fetch_candle_data, fetch_daily_data, filter_session_data,
    fetch_news, fetch_upcoming_events, has_high_impact_news_soon,
)
from indicators import compute_all_indicators, get_indicator_summary
from levels import compute_key_levels, levels_to_dataframe, detect_breaches, interpret_breaches
from signal_engine import generate_signal
from chart import build_chart


# -- Page config --
st.set_page_config(
    page_title="FX Dashboard - Prototype",
    page_icon="📊",
    layout="wide",
)

# -- Custom CSS for signal badges --
st.markdown("""
<style>
    .signal-long { color: #26a69a; font-size: 2rem; font-weight: bold; }
    .signal-short { color: #ef5350; font-size: 2rem; font-weight: bold; }
    .signal-stayout { color: #ffa726; font-size: 2rem; font-weight: bold; }
    .metric-card {
        background-color: #1e1e2f;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
    }
    .explanation-box {
        background-color: #1a1a2e;
        border-left: 4px solid #2196f3;
        padding: 1rem;
        border-radius: 4px;
        font-family: monospace;
        font-size: 0.9rem;
        white-space: pre-wrap;
    }
</style>
""", unsafe_allow_html=True)


def main():
    # ========== TOP ROW: Controls ==========
    st.title("FX Trading Dashboard")
    st.caption("Prototype - Decision Support Only (Not for Trade Execution)")

    col_pair, col_session, col_refresh, col_time = st.columns([1, 1, 0.5, 1.5])

    with col_pair:
        pair = st.selectbox("Pair", list(PAIRS.keys()), index=0)

    with col_session:
        session = st.selectbox("Session", list(SESSIONS.keys()), index=0)

    with col_refresh:
        st.write("")  # spacer
        refresh = st.button("Refresh", use_container_width=True)

    with col_time:
        st.write("")
        st.text(f"Last update: {dt.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")

    st.divider()

    # ========== FETCH DATA ==========
    with st.spinner("Loading market data..."):
        df_hourly = fetch_candle_data(pair)
        df_daily = fetch_daily_data(pair)

    if df_hourly.empty:
        st.error("No market data available. Please try again.")
        return

    # Filter to session
    df_session = filter_session_data(df_hourly, session)

    # ========== CALCULATIONS ==========
    indicators = compute_all_indicators(df_hourly)
    daily_indicators = compute_all_indicators(df_daily) if not df_daily.empty else None
    levels = compute_key_levels(df_hourly, session)
    breaches = detect_breaches(df_hourly, levels)
    breach_interp = interpret_breaches(breaches)
    news_blocking, news_desc = has_high_impact_news_soon(pair)
    news_items = fetch_news(pair)
    events = fetch_upcoming_events(pair)

    # ========== SIGNAL ==========
    result = generate_signal(
        indicators=indicators,
        daily_indicators=daily_indicators,
        levels=levels,
        breach_interpretation=breach_interp,
        news_blocking=news_blocking,
        news_desc=news_desc,
    )

    # ========== SUMMARY CARDS ==========
    c1, c2, c3, c4 = st.columns(4)

    current_price = indicators["current_price"]
    # Format price based on magnitude
    price_fmt = f"{current_price:.2f}" if current_price > 50 else f"{current_price:.5f}"

    with c1:
        st.metric("Current Price", price_fmt)

    with c2:
        signal = result["signal"]
        signal_class = {
            "LONG": "signal-long",
            "SHORT": "signal-short",
            "STAY OUT": "signal-stayout",
        }.get(signal, "signal-stayout")
        st.markdown(f"**Signal**")
        st.markdown(f'<div class="{signal_class}">{signal}</div>', unsafe_allow_html=True)

    with c3:
        confidence = result["confidence"]
        st.metric("Confidence", f"{confidence:.0f}%")

    with c4:
        st.metric("Market Regime", result["regime"])

    st.divider()

    # ========== MIDDLE LAYOUT ==========
    chart_col, info_col = st.columns([2, 1])

    with chart_col:
        fig = build_chart(df_hourly, indicators, levels, breaches, pair)
        st.plotly_chart(fig, use_container_width=True)

    with info_col:
        # Explanation box
        st.subheader("Signal Explanation")
        st.markdown(
            f'<div class="explanation-box">{result["explanation"]}</div>',
            unsafe_allow_html=True,
        )

        st.write("")

        # Indicator summary
        st.subheader("Indicators")
        ind_summary = get_indicator_summary(indicators)
        st.dataframe(
            pd.DataFrame(ind_summary),
            use_container_width=True,
            hide_index=True,
        )

        st.write("")

        # News & Events
        st.subheader("News & Events")

        if news_blocking:
            st.warning(f"⚠ High-impact event approaching: {news_desc}")

        for item in news_items:
            impact_color = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(item["impact"], "⚪")
            st.markdown(f"{impact_color} **{item['headline']}**")
            st.caption(f"{item['source']} | {item['timestamp']}")

        if events:
            st.markdown("**Upcoming Events:**")
            for ev in events:
                impact_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(ev["impact"], "⚪")
                st.markdown(f"{impact_icon} {ev['event']} — {ev['datetime']}")
                if ev.get("forecast"):
                    st.caption(f"Forecast: {ev['forecast']}")

    st.divider()

    # ========== BOTTOM LAYOUT ==========
    levels_col, breach_col = st.columns(2)

    with levels_col:
        st.subheader("Key Levels")
        levels_df = levels_to_dataframe(levels)
        if not levels_df.empty:
            # Format based on price magnitude
            dec = 2 if current_price > 50 else 5
            for col in ["High", "Low", "Range"]:
                levels_df[col] = levels_df[col].apply(lambda x: f"{x:.{dec}f}")
            st.dataframe(levels_df, use_container_width=True, hide_index=True)
        else:
            st.info("No level data available.")

    with breach_col:
        st.subheader("Recent Breaches")
        if breaches:
            breach_df = pd.DataFrame(breaches)
            # Reorder columns for readability
            display_cols = ["time", "level", "direction", "breach_type", "level_price", "candle_close"]
            available_cols = [c for c in display_cols if c in breach_df.columns]
            st.dataframe(
                breach_df[available_cols],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No recent breaches detected.")

    # ========== FOOTER ==========
    st.divider()
    st.caption(
        "Prototype Dashboard — Signal is rule-based and deterministic. "
        "News data is mocked for prototype. Not financial advice."
    )


if __name__ == "__main__":
    main()
