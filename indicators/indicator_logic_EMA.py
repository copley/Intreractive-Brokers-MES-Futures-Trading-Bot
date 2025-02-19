import logging

def calculate_EMA(prices: list, period: int):
    """
    Calculate the Exponential Moving Average (EMA) for the given list of prices and period.
    Returns the latest EMA value.
    """
    if not prices or period <= 0:
        return None
    # Use the standard EMA formula with smoothing factor k = 2/(period+1)&#8203;:contentReference[oaicite:0]{index=0}
    multiplier = 2 / (period + 1)
    ema = prices[0]  # start with first price as initial EMA (or could use SMA of first 'period' values)
    for price in prices[1:]:
        ema = (price * multiplier) + (ema * (1 - multiplier))  # EMA = Price_today * k + EMA_yesterday * (1-k)&#8203;:contentReference[oaicite:1]{index=1}
    logging.debug(f"Calculated EMA (period={period}) = {ema:.2f}")
    return ema
