"""
Chart module: premium Plotly candlestick chart with overlays and subplots.
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# Level line styles: (color, dash, width, annotation_side)
LEVEL_STYLES = {
    "Current Day":    ("#94a3b8", "solid",  0.9, "left"),
    "Previous Day":   ("#64748b", "dot",    0.8, "left"),
    "Current Week":   ("#38bdf8", "solid",  0.9, "left"),
    "Previous Week":  ("#0ea5e9", "dot",    0.8, "left"),
    "Current Month":  ("#a78bfa", "solid",  0.9, "left"),
    "Previous Month": ("#7c3aed", "dot",    0.8, "left"),
}

SESSION_STYLES = {
    "Asia":     ("#f59e0b", "dash", 0.9),
    "London":   ("#3b82f6", "dash", 0.9),
    "New York": ("#22c55e", "dash", 0.9),
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
    """Build a premium candlestick chart with indicators, levels, and breach markers."""
    recent = df.iloc[-show_bars:]

    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.025,
        row_heights=[0.62, 0.20, 0.18],
    )

    # ── Candlestick ──
    fig.add_trace(
        go.Candlestick(
            x=recent.index,
            open=recent["Open"], high=recent["High"],
            low=recent["Low"], close=recent["Close"],
            name="Price",
            increasing_line_color="#22c55e",
            decreasing_line_color="#ef4444",
            increasing_fillcolor="#22c55e",
            decreasing_fillcolor="#ef4444",
            line=dict(width=1),
        ),
        row=1, col=1,
    )

    # ── EMA overlays ──
    emas = [
        (20,  "_ema20_series",  "rgba(250, 204, 21, 0.7)",  1.0),
        (50,  "_ema50_series",  "rgba(59, 130, 246, 0.7)",  1.2),
        (200, "_ema200_series", "rgba(239, 68, 68, 0.6)",   1.6),
    ]
    for period, key, color, width in emas:
        series = indicators.get(key)
        if series is not None and not series.empty:
            s = series.loc[series.index.isin(recent.index)]
            if not s.empty:
                fig.add_trace(
                    go.Scatter(
                        x=s.index, y=s.values, mode="lines",
                        name=f"EMA {period}",
                        line=dict(color=color, width=width),
                    ),
                    row=1, col=1,
                )

    # ── Key level lines (only show most relevant to avoid clutter) ──
    for level_name, vals in levels.items():
        style = LEVEL_STYLES.get(level_name, ("#475569", "dot", 0.7, "left"))
        color, dash, width, ann_pos = style
        for side in ["high", "low"]:
            abbrev = _abbreviate(level_name, side)
            fig.add_hline(
                y=vals[side], line_dash=dash, line_color=color, line_width=width,
                annotation_text=abbrev, annotation_position=ann_pos,
                annotation_font_size=8, annotation_font_color=color,
                annotation_bgcolor="rgba(8,11,18,0.7)",
                row=1, col=1,
            )

    # ── Session level lines ──
    for sess_name, vals in session_levels.items():
        style = SESSION_STYLES.get(sess_name, ("#475569", "dash", 0.7))
        color, dash, width = style
        for side in ["high", "low"]:
            abbrev = _abbreviate_session(sess_name, side)
            fig.add_hline(
                y=vals[side], line_dash=dash, line_color=color, line_width=width,
                annotation_text=abbrev, annotation_position="right",
                annotation_font_size=8, annotation_font_color=color,
                annotation_bgcolor="rgba(8,11,18,0.7)",
                row=1, col=1,
            )

    # ── Breach markers ──
    for b in breaches:
        t = pd.Timestamp(b["time"])
        if t in recent.index:
            interp = b.get("interpretation", "")
            if interp == "Liquidity Sweep":
                color, symbol = "#a855f7", "diamond"
            elif interp == "Breakout":
                color = "#22c55e" if b["direction"] == "Above" else "#ef4444"
                symbol = "triangle-up" if b["direction"] == "Above" else "triangle-down"
            elif interp == "Reclaim":
                color, symbol = "#38bdf8", "circle"
            else:
                color, symbol = "#64748b", "x"

            fig.add_trace(
                go.Scatter(
                    x=[t], y=[b["level_price"]],
                    mode="markers",
                    marker=dict(size=8, color=color, symbol=symbol,
                                line=dict(width=0.8, color="rgba(255,255,255,0.4)")),
                    showlegend=False,
                    hovertext=f"{interp}: {b['level']}",
                    hoverinfo="text",
                ),
                row=1, col=1,
            )

    # ── RSI ──
    rsi = indicators.get("_rsi_series")
    if rsi is not None and not rsi.empty:
        rs = rsi.loc[rsi.index.isin(recent.index)]
        if not rs.empty:
            fig.add_trace(
                go.Scatter(x=rs.index, y=rs.values, mode="lines", name="RSI",
                           line=dict(color="#a78bfa", width=1.3)),
                row=2, col=1,
            )
            fig.add_hrect(y0=70, y1=100, fillcolor="rgba(239,68,68,0.04)", line_width=0, row=2, col=1)
            fig.add_hrect(y0=0, y1=30, fillcolor="rgba(34,197,94,0.04)", line_width=0, row=2, col=1)
            fig.add_hline(y=70, line_dash="dash", line_color="rgba(239,68,68,0.3)", line_width=0.6, row=2, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="rgba(34,197,94,0.3)", line_width=0.6, row=2, col=1)
            fig.add_hline(y=50, line_dash="dot", line_color="rgba(148,163,184,0.15)", line_width=0.5, row=2, col=1)

    # ── MACD ──
    macd_data = indicators.get("_macd")
    if macd_data:
        ml = macd_data["macd_line"].loc[macd_data["macd_line"].index.isin(recent.index)]
        sl = macd_data["signal_line"].loc[macd_data["signal_line"].index.isin(recent.index)]
        hs = macd_data["histogram"].loc[macd_data["histogram"].index.isin(recent.index)]

        if not hs.empty:
            colors = ["rgba(34,197,94,0.5)" if v >= 0 else "rgba(239,68,68,0.5)" for v in hs.values]
            fig.add_trace(
                go.Bar(x=hs.index, y=hs.values, name="Hist", marker_color=colors, showlegend=False),
                row=3, col=1,
            )
        if not ml.empty:
            fig.add_trace(
                go.Scatter(x=ml.index, y=ml.values, mode="lines", name="MACD",
                           line=dict(color="#38bdf8", width=1.1)),
                row=3, col=1,
            )
        if not sl.empty:
            fig.add_trace(
                go.Scatter(x=sl.index, y=sl.values, mode="lines", name="Signal",
                           line=dict(color="#f59e0b", width=1.1)),
                row=3, col=1,
            )

    # ── Layout ──
    fig.update_layout(
        template="plotly_dark",
        height=660,
        margin=dict(l=55, r=15, t=18, b=15),
        paper_bgcolor="#080b12",
        plot_bgcolor="#080b12",
        legend=dict(
            orientation="h", yanchor="bottom", y=1.005, xanchor="right", x=1,
            font=dict(size=9, color="#94a3b8"), bgcolor="rgba(0,0,0,0)",
        ),
        xaxis_rangeslider_visible=False,
        font=dict(family="Inter, sans-serif", color="#94a3b8", size=11),
        hoverlabel=dict(bgcolor="#1e293b", font_size=11, font_family="JetBrains Mono"),
    )

    grid_color = "rgba(148, 163, 184, 0.04)"
    for row in [1, 2, 3]:
        fig.update_yaxes(gridcolor=grid_color, zerolinecolor=grid_color, row=row, col=1)
        fig.update_xaxes(gridcolor=grid_color, row=row, col=1)

    fig.update_yaxes(title_text="", row=1, col=1)
    fig.update_yaxes(title_text="RSI", title_font_size=9, row=2, col=1, range=[0, 100])
    fig.update_yaxes(title_text="MACD", title_font_size=9, row=3, col=1)

    return fig


def _abbreviate(level_name: str, side: str) -> str:
    """Create short label for level annotations."""
    abbrevs = {
        "Current Day": "cD", "Previous Day": "pD",
        "Current Week": "cW", "Previous Week": "pW",
        "Current Month": "cM", "Previous Month": "pM",
    }
    prefix = abbrevs.get(level_name, level_name[:3])
    suffix = "H" if side == "high" else "L"
    return f"{prefix}{suffix}"


def _abbreviate_session(session_name: str, side: str) -> str:
    """Create short label for session level annotations."""
    abbrevs = {"Asia": "AS", "London": "LN", "New York": "NY"}
    prefix = abbrevs.get(session_name, session_name[:2])
    suffix = "H" if side == "high" else "L"
    return f"{prefix}{suffix}"
