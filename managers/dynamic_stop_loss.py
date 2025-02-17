import logging

class DynamicStopLoss:
    """
    Implements dynamic (trailing) stop-loss logic. Adjusts the stop-loss price as the trade moves in profit.
    """
    def __init__(self, initial_offset: float, trailing: bool = True):
        """
        initial_offset: initial stop distance (e.g., in price or percentage terms).
        trailing: if True, stop will trail the price when profitable.
        """
        self.initial_offset = initial_offset
        self.trailing = trailing
        self.initial_price = None
        self.current_stop = None

    def set_initial_stop(self, entry_price: float, position_type: str):
        """
        Set the initial stop price based on entry price and initial offset.
        """
        self.initial_price = entry_price
        if position_type.upper() == "LONG":
            # For long, stop below entry
            self.current_stop = entry_price - self.initial_offset
        else:
            # For short, stop above entry
            self.current_stop = entry_price + self.initial_offset
        logging.info(f"Initial stop-loss set at {self.current_stop:.4f} for {position_type} position.")
        return self.current_stop

    def update_stop(self, current_price: float, position_type: str):
        """
        Update the stop-loss price based on current price if trailing is enabled.
        Only move the stop in a favorable direction (up for longs, down for shorts).
        Returns the new stop price if updated, otherwise None.
        """
        if not self.trailing or self.current_stop is None or self.initial_price is None:
            # No trailing or no initial stop set
            return None
        new_stop = self.current_stop
        if position_type.upper() == "LONG":
            # For a long position: trail stop upward as price rises
            potential_stop = current_price - self.initial_offset
            if potential_stop > self.current_stop:
                new_stop = potential_stop
        else:
            # For a short position: trail stop downward as price falls
            potential_stop = current_price + self.initial_offset
            if potential_stop < self.current_stop:
                new_stop = potential_stop
        if new_stop != self.current_stop:
            self.current_stop = new_stop
            logging.info(f"Dynamic stop-loss updated to {new_stop:.4f} for {position_type} position.")
            return new_stop
        return None
