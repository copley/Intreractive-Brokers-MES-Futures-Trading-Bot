import logging

class TakeProfitManager:
    """
    Determines the take-profit price for a new trade and can be used to manage take-profit logic.
    """
    def __init__(self, take_profit_pct: float):
        # take_profit_pct is a fraction of entry price (e.g., 0.01 for 1%)
        self.take_profit_pct = take_profit_pct

    def get_take_profit_price(self, entry_price: float, position_type: str):
        """
        Calculate the take-profit price based on entry price and position type.
        For long positions, it's above entry; for short, it's below entry.
        """
        if position_type.upper() == "LONG":
            tp_price = entry_price * (1 + self.take_profit_pct)
        else:
            tp_price = entry_price * (1 - self.take_profit_pct)
        logging.info(f"TakeProfitManager: Take-profit set at {tp_price:.4f} for {position_type} position.")
        return tp_price
