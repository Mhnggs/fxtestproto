# FX Trading Dashboard - Prototype

A Streamlit-based Forex Trading Dashboard for **decision support only** (not trade execution).

Generates a directional bias — **LONG**, **SHORT**, or **STAY OUT** — for a selected FX pair and trading session using deterministic, rule-based logic.

## Supported Pairs
- EUR/USD
- GBP/USD
- USD/JPY

## Supported Sessions
- Day (full 24h)
- Asia (00:00–09:00 UTC)
- London (07:00–16:00 UTC)
- New York (12:00–21:00 UTC)

## Setup

### 1. Create a virtual environment (recommended)
```bash
python -m venv venv
source venv/bin/activate   # Linux/Mac
# or: venv\Scripts\activate  # Windows
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the dashboard
```bash
streamlit run app.py
```

The dashboard will open in your browser at `http://localhost:8501`.

## Project Structure

```
fxtestproto/
├── app.py              # Streamlit UI and layout
├── config.py           # Constants and configuration
├── data_fetcher.py     # Market data (yfinance) and news (mock)
├── indicators.py       # Technical indicator calculations
├── levels.py           # Key levels computation and breach detection
├── signal_engine.py    # Rule-based signal generation
├── chart.py            # Plotly chart builder
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

## What Is Real vs. Placeholder

| Component | Status |
|---|---|
| Market data (candles) | **Real** — pulled from Yahoo Finance via yfinance |
| Technical indicators (EMA, RSI, MACD, ATR) | **Real** — calculated from live data using the `ta` library |
| Key levels (day/week/month highs and lows) | **Real** — derived from actual candle data |
| Breach detection | **Real** — scans recent candles against computed levels |
| Signal engine | **Real** — deterministic weighted scoring of all components |
| News headlines | **Mock** — placeholder data; replace with a news API |
| Economic calendar/events | **Mock** — placeholder data; replace with calendar API |
| Fallback/synthetic data | Generated if Yahoo Finance is unavailable |

## Signal Logic (Summary)

1. **Trend**: Price vs EMA 200 (and EMA 50) on daily timeframe
2. **Momentum**: RSI 14 zones + MACD histogram direction
3. **Level positioning**: Price relative to prior day/week midpoints
4. **Breach behavior**: Wick vs close breaches of key levels
5. **News risk**: High-impact event proximity filter

Components are weighted and combined into a score:
- Score ≥ 0.3 → **LONG**
- Score ≤ -0.3 → **SHORT**
- Otherwise → **STAY OUT**

High-impact news approaching → forces **STAY OUT**.

## Manual Validation Suggestions

1. **Compare levels**: Open a chart on TradingView for the same pair and verify that the key levels (previous day high/low, etc.) match.
2. **Check indicators**: Compare EMA, RSI, MACD values against TradingView or another platform.
3. **Test each session**: Switch between Asia/London/New York and verify the session filter changes the data window.
4. **Test signal logic**: Mentally trace the explanation output against the rules in `signal_engine.py`.
5. **Test fallback mode**: Disconnect from the internet and verify the dashboard still loads with synthetic data.
6. **Edge cases**: Check behavior on weekends when markets are closed.

## Future Migration Path

The code is modular and separates data, logic, and UI:
- `data_fetcher.py` → FastAPI endpoint / service layer
- `indicators.py`, `levels.py`, `signal_engine.py` → business logic (unchanged)
- `app.py` → React frontend consuming the API
- Storage → PostgreSQL for historical data and signal logs

## Disclaimer

This is a prototype for testing purposes only. It does not constitute financial advice and should not be used for real trading decisions.
