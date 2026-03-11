"""
Chart module: builds Plotly candlestick charts with overlays, levels, and breach markers.
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd


# Color palette for level lines
LEVEL_COLORS = {
    "Current Day": "#ffffff",
    "Previous Day": "#90a4ae",
    "Current Week": "#4dd0e1",
    "Previous Week": "#0097a7",
    "Current Month": "#ce93d8",
    "Previous Month": "#7b1fa2",
}

SESSION_COLORS = {
    "Asia": "#ffb74d",
    "London": "#64b5f6",
    "New York": "#81c784",
}


def build_chart(
    df: pd.DataFrame,
    indicators: dict,
    levels: dict,
    session_levels: dict,
    breaches: list[dict],
    pair: str,
    show_bars: int = 120,
) -> go.Figure:
    """
    Build a professional candlestick chart with EMA overlays, key levels,
    session levels, and breach markers.
    """
    recent = df.iloc[-show_bars:]

    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.02,
        row_heights=[0.65, 0.20, 0.15],
    )

    # -- Candlestick --
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
            increasing_fillcolor="#26a69a",
            decreasing_fillcolor="#ef5350",
        ),
        row=1, col=1,
    )

    # -- EMA overlays --
    ema_config = [
        (20, "_ema20_series", "#ffeb3b", 1.2),
        (50, "_ema50_series", "#42a5f5", 1.5),
        (200, "_ema200_series", "#ff7043", 2.0),
    ]
    for period, key, color, width in ema_config:
        series = indicators.get(key)
        if series is not None and not series.empty:
            ema_slice = series.loc[series.index.isin(recent.index)]
            if not ema_slice.empty:
                fig.add_trace(
                    go.Scatter(
                        x=ema_slice.index, y=ema_slice.values,
                        mode="lines", name=f"EMA {period}",
                        line=dict(color=color, width=width),
                    ),
                    row=1, col=1,
                )

    # -- Key level lines --
    for level_name, vals in levels.items():
        color = LEVEL_COLORS.get(level_name, "#78909c")
        for side in ["high", "low"]:
            label = f"{level_name} {'H' if side == 'high' else 'L'}"
            fig.add_hline(
                y=vals[side], line_dash="dot", line_color=color, line_width=1,
                annotation_text=label, annotation_position="left",
                annotation_font_size=9, annotation_font_color=color,
                row=1, col=1,
            )

    # -- Session level lines --
    for session_name, vals in session_levels.items():
        color = SESSION_COLORS.get(session_name, "#bdbdbd")
        for side in ["high", "low"]:
            label = f"{session_name} {'H' if side == 'high' else 'L'}"
            fig.add_hline(
                y=vals[side], line_dash="dash", line_color=color, line_width=1.2,
                annotation_text=label, annotation_position="right",
                annotation_font_size=9, annotation_font_color=color,
                row=1, col=1,
            )

    # -- Breach markers --
    for b in breaches:
        breach_time = pd.Timestamp(b["time"])
        if breach_time in recent.index:
            is_sweep = b.get("interpretation") == "Liquidity Sweep"
            marker_color = "#ff9800" if b["breach_type"] == "Wick" else "#f44336"
            if is_sweep:
                marker_color = "#e040fb"
            marker_symbol = "triangle-up" if b["direction"] == "Above" else "triangle-down"
            fig.add_trace(
                go.Scatter(
                    x=[breach_time], y=[b["level_price"]],
                    mode="markers",
                    marker=dict(size=10, color=marker_color, symbol=marker_symbol,
                                line=dict(width=1, color="#ffffff")),
                    name=f"{b.get('interpretation', 'Breach')}: {b['level']}",
                    showlegend=False,
                    hovertext=f"{b.get('interpretation', b['breach_type'])} {b['direction']} {b['level']}",
                ),
                row=1, col=1,
            )

    # -- RSI subplot --
    rsi_series = indicators.get("_rsi_series")
    if rsi_series is not None and not rsi_series.empty:
        rsi_slice = rsi_series.loc[rsi_series.index.isin(recent.index)]
        if not rsi_slice.empty:
            fig.add_trace(
                go.Scatter(
                    x=rsi_slice.index, y=rsi_slice.values,
                    mode="lines", name="RSI",
                    line=dict(color="#ab47bc", width=1.5),
                ),
                row=2, col=1,
            )
            fig.add_hline(y=70, line_dash="dash", line_color="#ef5350", line_width=0.7, row=2, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="#26a69a", line_width=0.7, row=2, col=1)
            fig.add_hline(y=50, line_dash="dot", line_color="#546e7a", line_width=0.5, row=2, col=1)

    # -- MACD subplot --
    macd_data = indicators.get("_macd")
    if macd_data:
        macd_line = macd_data["macd_line"]
        signal_line = macd_data["signal_line"]
        histogram = macd_data["histogram"]

        macd_slice = macd_line.loc[macd_line.index.isin(recent.index)]
        sig_slice = signal_line.loc[signal_line.index.isin(recent.index)]
        hist_slice = histogram.loc[histogram.index.isin(recent.index)]

        if not hist_slice.empty:
            colors = ["#26a69a" if v >= 0 else "#ef5350" for v in hist_slice.values]
            fig.add_trace(
                go.Bar(
                    x=hist_slice.index, y=hist_slice.values,
                    name="MACD Hist", marker_color=colors, opacity=0.6,
                ),
                row=3, col=1,
            )
        if not macd_slice.empty:
            fig.add_trace(
                go.Scatter(
                    x=macd_slice.index, y=macd_slice.values,
                    mode="lines", name="MACD",
                    line=dict(color="#42a5f5", width=1.2),
                ),
                row=3, col=1,
            )
        if not sig_slice.empty:
            fig.add_trace(
                go.Scatter(
                    x=sig_slice.index, y=sig_slice.values,
                    mode="lines", name="Signal",
                    line=dict(color="#ff7043", width=1.2),
                ),
                row=3, col=1,
            )

    # -- Layout --
    fig.update_layout(
        template="plotly_dark",
        height=700,
        margin=dict(l=50, r=20, t=30, b=20),
        paper_bgcolor="#0e1117",
        plot_bgcolor="#0e1117",
        legend=dict(
            orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1,
            font=dict(size=10), bgcolor="rgba(0,0,0,0)",
        ),
        xaxis_rangeslider_visible=False,
        font=dict(color="#e0e0e0"),
    )

    fig.update_yaxes(title_text="Price", row=1, col=1, gridcolor="#1e1e2f")
    fig.update_yaxes(title_text="RSI", row=2, col=1, range=[0, 100], gridcolor="#1e1e2f")
    fig.update_yaxes(title_text="MACD", row=3, col=1, gridcolor="#1e1e2f")
    fig.update_xaxes(gridcolor="#1e1e2f")

    return fig
