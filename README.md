# FX Trading Dashboard - Prototype v2

A professional-looking Streamlit-based Forex Trading Dashboard for **decision support only**.

Generates a directional bias — **LONG**, **SHORT**, or **STAY OUT** — using deterministic, rule-based logic with transparent scoring.

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
├── app.py                # Entry point (launches ui_dashboard)
├── ui_dashboard.py       # Streamlit UI layout and rendering
├── config.py             # Constants, pairs, sessions, weights, thresholds
├── data_fetcher.py       # Market data via yfinance + synthetic fallback
├── indicator_engine.py   # EMA, RSI, MACD, ATR calculations
├── level_engine.py       # Day/week/month key levels + distance calc
├── session_engine.py     # Session-specific levels (Asia/London/NY)
├── breach_detector.py    # Breach detection + liquidity sweep identification
├── signal_engine.py      # Weighted rule-based signal generation
├── news_engine.py        # News headlines + economic calendar (mock)
├── chart.py              # Plotly chart with overlays, levels, breach markers
├── requirements.txt      # Python dependencies
└── README.md
```

## Dashboard Sections

| Section | Description |
|---|---|
| **Summary Cards** | Current price, signal (color-coded), confidence gauge, market regime |
| **Chart** | Candlestick with EMA 20/50/200, key levels, session levels, breach markers, RSI + MACD subplots |
| **Signal Explanation** | Human-readable reasoning for the directional bias |
| **Score Breakdown** | Transparent per-component scoring (trend, momentum, structure, breach, news) |
| **Indicators** | Current readings for all technical indicators |
| **Market Conditions** | Trend, volatility, session range % of ATR, market state |
| **News & Events** | Headlines, next macro event, risk status (Clear/Caution/Block) |
| **Liquidity Events** | Detected sweeps of session and key levels |
| **Key Levels** | Day/week/month highs and lows with distance from current price in pips |
| **Session Levels** | Asia/London/NY highs and lows with range in pips |
| **Breach Analysis** | Time, level, direction, breach type, interpretation (Sweep/Breakout/Reclaim) |
| **Debug Mode** | Toggle to show raw indicator values, component scores, and breach details |

## What Is Real vs. Mock

| Component | Status |
|---|---|
| Market data (candles) | **Real** — Yahoo Finance via yfinance |
| Technical indicators | **Real** — pure pandas/numpy calculations |
| Key levels | **Real** — computed from actual candle data |
| Session levels | **Real** — filtered by session UTC hours |
| Breach detection | **Real** — scans candles against computed levels |
| Liquidity sweeps | **Real** — wick-beyond-close detection logic |
| Signal engine | **Real** — deterministic weighted scoring |
| News headlines | **Mock** — replace with news API |
| Economic calendar | **Mock** — replace with calendar API |
| Fallback data | Synthetic — generated when Yahoo Finance unavailable |

## Signal Logic

1. **Trend** (30%): Price vs EMA 200 + EMA 50 on daily timeframe
2. **Momentum** (25%): RSI 14 zones + MACD histogram direction
3. **Structure** (20%): Price relative to prior day/week midpoints
4. **Breach** (15%): Wick vs close breaches, sweep detection
5. **News** (10%): High-impact event proximity filter

Score ≥ 0.3 → **LONG** | Score ≤ -0.3 → **SHORT** | Otherwise → **STAY OUT**

## Verification Against TradingView

1. Open the same pair on TradingView (1H timeframe)
2. Add EMA 20, 50, 200 — compare values
3. Add RSI 14 — compare reading
4. Compare previous day/week highs and lows
5. Check that the signal explanation aligns with what you see on the chart

## Disclaimer

Prototype for testing purposes only. Not financial advice.
