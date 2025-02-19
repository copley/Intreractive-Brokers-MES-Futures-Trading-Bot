import logging

def calculate_RSI(prices: list, period: int = 14):
    """
    Calculate the Relative Strength Index (RSI) for the given list of prices and look-back period.
    Returns the latest RSI value.
    """
    if len(prices) < period + 1:
        # Not enough data to calculate RSI
        return None
    # Calculate price changes
    gains = 0.0
    losses = 0.0
    for i in range(1, period+1):
        change = prices[i] - prices[i-1]
        if change >= 0:
            gains += change
        else:
            losses += -change
    # Calculate average gain and loss
    avg_gain = gains / period
    avg_loss = losses / period
    # Edge case: if no losses, RSI is 100; if no gains, RSI is 0
    if avg_loss == 0:
        return 100.0
    if avg_gain == 0:
        return 0.0
    # Calculate RSI using formula RSI = 100 - 100/(1 + RS)&#8203;:contentReference[oaicite:2]{index=2}
    RS = avg_gain / avg_loss
    RSI = 100 - (100 / (1 + RS))
    logging.debug(f"Calculated RSI (period={period}) = {RSI:.2f}")
    return RSI
