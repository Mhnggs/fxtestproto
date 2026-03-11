"""
Configuration constants for the Forex Trading Dashboard prototype.
"""

# Supported currency pairs and their Yahoo Finance tickers
PAIRS = {
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "USDJPY": "USDJPY=X",
}

# Currency components for news filtering
PAIR_CURRENCIES = {
    "EURUSD": ["EUR", "USD"],
    "GBPUSD": ["GBP", "USD"],
    "USDJPY": ["USD", "JPY"],
}

# Trading sessions with UTC hour ranges
SESSIONS = {
    "Day": (0, 24),       # Full day
    "Asia": (0, 9),       # 00:00 - 09:00 UTC
    "London": (7, 16),    # 07:00 - 16:00 UTC
    "New York": (12, 21), # 12:00 - 21:00 UTC
}

# Indicator parameters
EMA_PERIODS = [20, 50, 200]
RSI_PERIOD = 14
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
ATR_PERIOD = 14

# Signal engine weights
WEIGHTS = {
    "trend": 0.30,
    "momentum": 0.25,
    "levels": 0.20,
    "breach": 0.15,
    "news": 0.10,
}

# Thresholds
RSI_BULLISH = 55
RSI_BEARISH = 45
SIGNAL_LONG_THRESHOLD = 0.3
SIGNAL_SHORT_THRESHOLD = -0.3
