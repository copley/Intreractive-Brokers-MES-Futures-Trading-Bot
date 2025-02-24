# File: indicators/indicator_logic_ATR.py

import pandas as pd
import logging

def calculate_ATR_series(df, high_col='high', low_col='low', close_col='close', period=14):
    """
    Existing function: Return a pandas Series with the ATR for each row in df.
    """
    for col in [high_col, low_col, close_col]:
        if col not in df.columns:
            logging.error(f"DataFrame missing column '{col}' for ATR.")
            return pd.Series([None]*len(df))

    prev_close = df[close_col].shift(1)
    high_low = df[high_col] - df[low_col]
    high_prevclose = (df[high_col] - prev_close).abs()
    low_prevclose = (df[low_col] - prev_close).abs()

    tr = pd.concat([high_low, high_prevclose, low_prevclose], axis=1).max(axis=1)
    atr = tr.ewm(span=period, adjust=False).mean()
    return atr

def calculate_ATR(highs, lows, closes, period=14):
    """
    NEW array-based helper:
    Calculate the ATR from Python lists: `highs`, `lows`, `closes`.
    Returns the *latest* ATR value (float), or None if not enough data.
    """
    if not highs or not lows or not closes:
        return None
    if len(highs) < period + 1 or len(lows) < period + 1 or len(closes) < period + 1:
        return None

    df = pd.DataFrame({
        'high': highs,
        'low':  lows,
        'close': closes
    })

    # We can re-use the logic above
    prev_close = df['close'].shift(1)
    high_low = df['high'] - df['low']
    high_prevclose = (df['high'] - prev_close).abs()
    low_prevclose = (df['low'] - prev_close).abs()

    tr = pd.concat([high_low, high_prevclose, low_prevclose], axis=1).max(axis=1)
    atr_series = tr.ewm(span=period, adjust=False).mean()

    # Return the most recent ATR value
    return atr_series.iloc[-1]
