import logging

class EntryManager:
    """
    Determines entry signals based on indicator values and strategy rules.
    """
    def __init__(self, strategy_config: dict):
        # Load strategy thresholds (like RSI overbought/oversold levels) from config
        self.rsi_overbought = strategy_config.get('RSI_overbought', 70)
        self.rsi_oversold = strategy_config.get('RSI_oversold', 30)
        self.last_signal = None

    def evaluate_entry(self, data_point: dict, indicators: dict):
        """
        Evaluate indicators and price data to decide whether to enter a trade.
        Returns a signal dict if entry criteria are met, otherwise None.
        """
        signal = None
        price = data_point.get('close')
        if price is None:
            return None
        ema_value = indicators.get('EMA')
        rsi_value = indicators.get('RSI')
        # Example strategy:
        # If RSI indicates oversold and price crosses above EMA -> go long.
        # If RSI indicates overbought and price crosses below EMA -> go short.
        if rsi_value is not None and ema_value is not None:
            if rsi_value < self.rsi_oversold and price > ema_value:
                signal = {'type': 'LONG', 'reason': 'RSI oversold and price > EMA'}
            elif rsi_value > self.rsi_overbought and price < ema_value:
                signal = {'type': 'SHORT', 'reason': 'RSI overbought and price < EMA'}
        # Additional entry conditions (e.g., using ATR, VWAP) could be added here.
        if signal:
            logging.info(f"EntryManager: Entry signal detected -> {signal}")
        self.last_signal = signal
        return signal
