# File: indicators/indicator_logic_EMA.py

import pandas as pd
import logging

def calculate_EMA_series(df, price_col='close', period=20):
    """
    Existing function: Return a pandas Series with the EMA for each row in df[price_col].
    """
    if price_col not in df.columns:
        logging.error(f"DataFrame has no column '{price_col}'")
        return pd.Series([None] * len(df))

    if period <= 0:
        logging.error("EMA period must be > 0.")
        return pd.Series([None] * len(df))

    ema_series = df[price_col].ewm(span=period, adjust=False).mean()
    return ema_series

def calculate_EMA(prices, period=20):
    """
    NEW array-based helper:
    Calculate the EMA of a simple list of `prices`.
    Returns the *latest* EMA (a float), or None if not enough data.
    """
    if not prices:
        return None
    if period <= 0:
        logging.error("EMA period must be > 0.")
        return None

    # Convert to pandas Series and use ewm
    s = pd.Series(prices)
    ema_series = s.ewm(span=period, adjust=False).mean()
    # Return the most recent EMA
    return ema_series.iloc[-1]
