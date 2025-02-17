import logging

class ExitManager:
    """
    Determines exit signals (aside from stop-loss or take-profit triggers) based on indicators or other criteria.
    """
    def __init__(self):
        self.last_exit_signal = None

    def evaluate_exit(self, data_point: dict, indicators: dict, position: dict):
        """
        Evaluate whether to exit an open position based on current indicators and price.
        Returns an exit signal dict if criteria met, otherwise None.
        """
        if position is None:
            return None  # no position to evaluate exit for
        exit_signal = None
        pos_type = position.get('type')
        price = data_point.get('close')
        ema_value = indicators.get('EMA')
        rsi_value = indicators.get('RSI')
        # Example exit strategy:
        # If in a long position and price falls back below EMA or RSI rises above 50 (loss of momentum) -> exit.
        if pos_type == 'LONG':
            if ema_value is not None and price is not None and price < ema_value:
                exit_signal = {'type': 'EXIT', 'position_type': 'LONG', 'reason': 'Price fell below EMA'}
            elif rsi_value is not None and rsi_value > 50 and price is not None and price < position.get('entry_price', price):
                exit_signal = {'type': 'EXIT', 'position_type': 'LONG', 'reason': 'RSI high, momentum lost'}
        elif pos_type == 'SHORT':
            if ema_value is not None and price is not None and price > ema_value:
                exit_signal = {'type': 'EXIT', 'position_type': 'SHORT', 'reason': 'Price rose above EMA'}
            elif rsi_value is not None and rsi_value < 50 and price is not None and price > position.get('entry_price', price):
                exit_signal = {'type': 'EXIT', 'position_type': 'SHORT', 'reason': 'RSI low, momentum lost'}
        if exit_signal:
            logging.info(f"ExitManager: Exit signal detected -> {exit_signal}")
        self.last_exit_signal = exit_signal
        return exit_signal
