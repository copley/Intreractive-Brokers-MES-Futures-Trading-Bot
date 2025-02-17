import logging
from managers.dynamic_stop_loss import DynamicStopLoss

class StopLossManager:
    """
    Manages stop-loss updates using dynamic stop-loss logic.
    """
    def __init__(self, dynamic_stop_loss: DynamicStopLoss):
        self.dynamic_stop_loss = dynamic_stop_loss

    def set_initial_stop(self, entry_price: float, position_type: str):
        """
        Set the initial stop loss when a new trade is opened.
        """
        return self.dynamic_stop_loss.set_initial_stop(entry_price, position_type)

    def update_stop_loss(self, current_price: float, position_type: str):
        """
        Update the stop-loss based on current price for trailing stop logic.
        Returns new stop price if updated, otherwise None.
        """
        new_stop = self.dynamic_stop_loss.update_stop(current_price, position_type)
        if new_stop:
            logging.info(f"StopLossManager: Stop-loss updated to {new_stop:.4f}")
        return new_stop
