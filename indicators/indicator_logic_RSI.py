# File: indicators/indicator_logic_RSI.py

import pandas as pd
import logging

def calculate_RSI_series(df, price_col='close', period=14):
    """
    Existing function: Return a pandas Series with the RSI for each row in df[price_col].
    """
    if price_col not in df.columns:
        logging.error(f"DataFrame has no column '{price_col}' for RSI.")
        return pd.Series([None] * len(df))

    if len(df) < period + 1:
        logging.warning("Not enough rows to compute RSI for all rows.")

    # Price changes
    delta = df[price_col].diff()
    gain = delta.where(delta > 0, other=0.0)
    loss = -delta.where(delta < 0, other=0.0)

    avg_gain = gain.ewm(span=period, adjust=False).mean()
    avg_loss = loss.ewm(span=period, adjust=False).mean()

    rs = avg_gain / avg_loss
    rsi = 100.0 - (100.0 / (1.0 + rs))

    rsi = rsi.fillna(method='bfill').fillna(50.0)
    return rsi

def calculate_RSI(prices, period=14):
    """
    NEW array-based helper:
    Calculate RSI on a list of `prices`. Returns the *latest* RSI float.
    """
    if not prices:
        return None
    if len(prices) < period + 1:
        # Not enough bars; return a neutral 50 or None
        return 50.0

    s = pd.Series(prices)
    delta = s.diff()

    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)

    avg_gain = gain.ewm(span=period, adjust=False).mean()
    avg_loss = loss.ewm(span=period, adjust=False).mean()

    rs = avg_gain / avg_loss
    rsi_series = 100.0 - (100.0 / (1.0 + rs))

    # Return the most recent RSI value
    return rsi_series.iloc[-1]
