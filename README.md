# FX Trading Dashboard

A premium Streamlit-based Forex Trading Dashboard for directional bias analysis.

Generates **LONG**, **SHORT**, or **STAY OUT** signals using deterministic, rule-based logic with transparent scoring.

## Supported Pairs
- EUR/USD
- GBP/USD
- USD/JPY

## Supported Sessions
- Day (full 24h)
- Asia (00:00–09:00 UTC)
- London (07:00–16:00 UTC)
- New York (12:00–21:00 UTC)

## Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

Opens at `http://localhost:8501`.

## Project Structure

```
fxtestproto/
├── app.py                # Entry point
├── ui_dashboard.py       # Dashboard layout and rendering
├── styles.py             # Premium CSS theme
├── config.py             # Constants, pairs, sessions, weights
├── data_fetcher.py       # Market data via yfinance + fallback
├── indicator_engine.py   # EMA, RSI, MACD, ATR calculations
├── level_engine.py       # Key levels + breach status classification
├── session_engine.py     # Session-specific levels (Asia/London/NY)
├── breach_detector.py    # Breach detection + liquidity sweep ID
├── signal_engine.py      # Weighted rule-based signal generation
├── news_engine.py        # News headlines + economic calendar
├── chart.py              # Premium Plotly chart with overlays
├── requirements.txt      # Dependencies
└── README.md
```

## Dashboard Sections

| Section | Description |
|---|---|
| **Alert Bar** | Top-level breach alerts with color-coded severity |
| **Summary Cards** | Price, signal, confidence gauge, market regime |
| **Chart** | Candlestick with EMAs, key levels, session levels, breach markers, RSI + MACD |
| **Signal Explanation** | Component-by-component reasoning |
| **Score Breakdown** | Visual per-component scoring with mini bars |
| **Indicators** | Current technical indicator readings |
| **Market Conditions** | Trend, volatility, session range % of ATR |
| **News & Events** | Headlines, next macro event, risk status |
| **Liquidity Events** | Detected session and key level sweeps |
| **Key Levels** | Highs/lows with pip distance and breach status |
| **Session Levels** | Asia/London/NY with range in pips |
| **Breach Analysis** | Timestamped event log with interpretations |
| **Debug Mode** | Expandable raw data for validation |

## Signal Logic

1. **Trend** (30%): Price vs EMA 200 + EMA 50 on daily timeframe
2. **Momentum** (25%): RSI 14 zones + MACD histogram direction
3. **Structure** (20%): Price relative to prior day/week midpoints
4. **Breach** (15%): Wick vs close breaches, sweep detection
5. **News** (10%): High-impact event proximity filter

Score >= 0.3 → **LONG** · Score <= -0.3 → **SHORT** · Otherwise → **STAY OUT**

## Verification Against TradingView

1. Open the same pair on TradingView (1H timeframe)
2. Add EMA 20, 50, 200 — compare values
3. Add RSI 14 — compare reading
4. Compare previous day/week highs and lows
5. Check that the signal explanation aligns with chart visuals

## Disclaimer

Not financial advice. Rule-based signals for analysis purposes only.
