import logging

def calculate_VWAP(prices: list, volumes: list):
    """
    Calculate the Volume-Weighted Average Price (VWAP) for given price and volume lists.
    VWAP = sum(price_i * volume_i) / sum(volume_i)&#8203;:contentReference[oaicite:6]{index=6}.
    """
    if not prices or not volumes or len(prices) != len(volumes):
        return None
    total_volume = sum(volumes)
    if total_volume == 0:
        return None
    # Compute VWAP as the weighted average of prices by volume&#8203;:contentReference[oaicite:7]{index=7}
    weighted_sum = 0.0
    for price, vol in zip(prices, volumes):
        weighted_sum += price * vol
    vwap = weighted_sum / total_volume
    logging.debug(f"Calculated VWAP = {vwap:.4f}")
    return vwap
