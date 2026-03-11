"""
Chart module: builds Plotly candlestick charts with overlays.
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd


def build_chart(
    df: pd.DataFrame,
    indicators: dict,
    levels: dict,
    breaches: list[dict],
    pair: str,
    show_bars: int = 100,
) -> go.Figure:
    """
    Build a candlestick chart with EMA overlays, key levels, and breach markers.

    Args:
        df: OHLCV DataFrame
        indicators: Dict containing indicator series (keys prefixed with _)
        levels: Key levels dict
        breaches: List of breach event dicts
        pair: Pair name for title
        show_bars: Number of recent bars to display

    Returns:
        Plotly Figure
    """
    recent = df.iloc[-show_bars:]

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.75, 0.25],
        subplot_titles=[f"{pair} - 1H Chart", "RSI"],
    )

    # Candlestick
    fig.add_trace(
        go.Candlestick(
            x=recent.index,
            open=recent["Open"],
            high=recent["High"],
            low=recent["Low"],
            close=recent["Close"],
            name="Price",
            increasing_line_color="#26a69a",
            decreasing_line_color="#ef5350",
        ),
        row=1, col=1,
    )

    # EMA overlays
    ema_colors = {20: "#ffeb3b", 50: "#2196f3", 200: "#ff5722"}
    for period, key in [(20, "_ema20_series"), (50, "_ema50_series"), (200, "_ema200_series")]:
        series = indicators.get(key)
        if series is not None and not series.empty:
            ema_slice = series.loc[series.index.isin(recent.index)]
            if not ema_slice.empty:
                fig.add_trace(
                    go.Scatter(
                        x=ema_slice.index,
                        y=ema_slice.values,
                        mode="lines",
                        name=f"EMA {period}",
                        line=dict(color=ema_colors[period], width=1.5),
                    ),
                    row=1, col=1,
                )

    # Key level lines
    level_colors = {
        "Current Day": "#ffffff",
        "Previous Day": "#b0bec5",
        "Current Week": "#80cbc4",
        "Previous Week": "#4db6ac",
        "Current Month": "#ce93d8",
        "Previous Month": "#ab47bc",
    }

    for level_name, vals in levels.items():
        color = level_colors.get(level_name, "#90a4ae")
        for side in ["high", "low"]:
            fig.add_hline(
                y=vals[side],
                line_dash="dot",
                line_color=color,
                line_width=1,
                annotation_text=f"{level_name} {'H' if side == 'high' else 'L'}",
                annotation_position="left",
                annotation_font_size=9,
                annotation_font_color=color,
                row=1, col=1,
            )

    # Breach markers
    for b in breaches:
        breach_time = pd.Timestamp(b["time"])
        if breach_time in recent.index:
            marker_color = "#ff9800" if b["breach_type"] == "wick" else "#f44336"
            marker_symbol = "triangle-up" if b["direction"] == "above" else "triangle-down"
            fig.add_trace(
                go.Scatter(
                    x=[breach_time],
                    y=[b["level_price"]],
                    mode="markers",
                    marker=dict(size=10, color=marker_color, symbol=marker_symbol),
                    name=f"Breach: {b['level']}",
                    showlegend=False,
                    hovertext=f"{b['breach_type']} {b['direction']} {b['level']}",
                ),
                row=1, col=1,
            )

    # RSI subplot
    rsi_series = indicators.get("_rsi_series")
    if rsi_series is not None and not rsi_series.empty:
        rsi_slice = rsi_series.loc[rsi_series.index.isin(recent.index)]
        if not rsi_slice.empty:
            fig.add_trace(
                go.Scatter(
                    x=rsi_slice.index,
                    y=rsi_slice.values,
                    mode="lines",
                    name="RSI",
                    line=dict(color="#ab47bc", width=1.5),
                ),
                row=2, col=1,
            )
            # RSI reference lines
            fig.add_hline(y=70, line_dash="dash", line_color="#ef5350", line_width=0.8, row=2, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="#26a69a", line_width=0.8, row=2, col=1)
            fig.add_hline(y=50, line_dash="dot", line_color="#607d8b", line_width=0.5, row=2, col=1)

    # Layout styling
    fig.update_layout(
        template="plotly_dark",
        height=600,
        margin=dict(l=50, r=20, t=40, b=20),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=10),
        ),
        xaxis_rangeslider_visible=False,
    )

    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="RSI", row=2, col=1, range=[0, 100])

    return fig
