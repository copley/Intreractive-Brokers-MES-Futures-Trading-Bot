import logging

def calculate_ATR(highs: list, lows: list, closes: list, period: int = 14):
    """
    Calculate the Average True Range (ATR) for given high, low, close price series and period.
    Returns the latest ATR value.
    """
    if len(highs) < period+1 or len(lows) < period+1 or len(closes) < period+1:
        return None
    # Calculate True Range (TR) for each period&#8203;:contentReference[oaicite:3]{index=3}
    true_ranges = []
    for i in range(1, len(highs)):
        high = highs[i]
        low = lows[i]
        prev_close = closes[i-1]
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        true_ranges.append(tr)
    # Calculate initial ATR as simple average of first 'period' true ranges&#8203;:contentReference[oaicite:4]{index=4}
    initial_atr = sum(true_ranges[:period]) / period
    atr = initial_atr
    # Wilder's smoothing: subsequent ATR = ((previous ATR * (period - 1)) + current TR) / period&#8203;:contentReference[oaicite:5]{index=5}
    for tr in true_ranges[period:]:
        atr = ((atr * (period - 1)) + tr) / period
    logging.debug(f"Calculated ATR (period={period}) = {atr:.4f}")
    return atr
