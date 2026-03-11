"""
Technical indicator calculations.
Pure pandas/numpy implementation — no external ta library needed.
"""

import pandas as pd
import numpy as np


def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    """Calculate Exponential Moving Average."""
    return series.ewm(span=period, adjust=False).mean()


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Relative Strength Index."""
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def calculate_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> dict:
    """Calculate MACD line, signal line, and histogram."""
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return {"macd_line": macd_line, "signal_line": signal_line, "histogram": histogram}


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate Average True Range."""
    tr1 = df["High"] - df["Low"]
    tr2 = (df["High"] - df["Close"].shift(1)).abs()
    tr3 = (df["Low"] - df["Close"].shift(1)).abs()
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return true_range.ewm(span=period, adjust=False).mean()


def compute_all_indicators(df: pd.DataFrame) -> dict:
    """
    Compute all core indicators. Returns latest scalar values and full series
    (prefixed with _) for charting.
    """
    close = df["Close"]
    ema20 = calculate_ema(close, 20)
    ema50 = calculate_ema(close, 50)
    ema200 = calculate_ema(close, 200)
    rsi = calculate_rsi(close)
    macd = calculate_macd(close)
    atr = calculate_atr(df)

    current_price = close.iloc[-1]

    return {
        "current_price": current_price,
        "ema_20": ema20.iloc[-1] if not ema20.empty else None,
        "ema_50": ema50.iloc[-1] if not ema50.empty else None,
        "ema_200": ema200.iloc[-1] if not ema200.empty else None,
        "rsi": rsi.iloc[-1] if not rsi.empty else None,
        "macd_line": macd["macd_line"].iloc[-1] if not macd["macd_line"].empty else None,
        "macd_signal": macd["signal_line"].iloc[-1] if not macd["signal_line"].empty else None,
        "macd_histogram": macd["histogram"].iloc[-1] if not macd["histogram"].empty else None,
        "atr": atr.iloc[-1] if not atr.empty else None,
        # Full series for charting
        "_ema20_series": ema20,
        "_ema50_series": ema50,
        "_ema200_series": ema200,
        "_rsi_series": rsi,
        "_macd": macd,
        "_atr_series": atr,
    }


def get_indicator_summary(indicators: dict) -> list[dict]:
    """Format indicators into a display-friendly list of dicts."""
    price = indicators.get("current_price", 1.0)
    dec = 2 if price > 50 else 5

    def fmt(val, decimals=5):
        if val is None or (isinstance(val, float) and np.isnan(val)):
            return "N/A"
        return f"{val:.{decimals}f}"

    return [
        {"Indicator": "EMA 20", "Value": fmt(indicators["ema_20"], dec)},
        {"Indicator": "EMA 50", "Value": fmt(indicators["ema_50"], dec)},
        {"Indicator": "EMA 200", "Value": fmt(indicators["ema_200"], dec)},
        {"Indicator": "RSI (14)", "Value": fmt(indicators["rsi"], 2)},
        {"Indicator": "MACD Line", "Value": fmt(indicators["macd_line"], dec)},
        {"Indicator": "MACD Signal", "Value": fmt(indicators["macd_signal"], dec)},
        {"Indicator": "MACD Hist", "Value": fmt(indicators["macd_histogram"], dec)},
        {"Indicator": "ATR (14)", "Value": fmt(indicators["atr"], dec)},
    ]
