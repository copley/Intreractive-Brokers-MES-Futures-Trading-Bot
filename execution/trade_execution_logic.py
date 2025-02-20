# File: execution/trade_execution_logic.py

import logging
from execution.long_order_execution_logic import execute_long_order
from execution.short_order_execution_logic import execute_short_order
from execution.limit_order_execution_logic import execute_limit_order
from execution.stop_loss_order_execution_logic import place_stop_loss_order

class TradeExecutor:
    """
    Coordinates trade execution logic, deciding whether to execute long, short, or exit trades
    using the appropriate order functions.
    """
    def __init__(self, ib_connection, contract, config):
        self.ib = ib_connection  # might be None in backtest
        self.contract = contract # might be None in backtest
        self.config = config     # store config for reference

    def execute_trade(self, signal: dict):
        """
        The signal dictionary is expected to have keys:
        - type: "LONG", "SHORT", or "EXIT"
        - quantity
        - price
        - stop_loss
        - take_profit
        - position_type (for "EXIT")
        """
        trade_type = signal.get('type')
        quantity = signal.get('quantity', 0)
        price = signal.get('price', None)

        # If no IB connection, we are in backtest mode => skip real order
        if self.ib is None or self.contract is None:
            logging.info(f"[Backtest Mode] Would execute {trade_type} order, qty={quantity}, price={price}")
            # Optionally do more logging or simulated fills
            return

        # Otherwise place real IB order
        if trade_type == "LONG":
            logging.info(f"TradeExecutor: Initiating LONG position for quantity {quantity}")
            execute_long_order(self.ib, self.contract, quantity, limit_price=price)
            if signal.get('stop_loss'):
                place_stop_loss_order(self.ib, self.contract, quantity, signal['stop_loss'], position_type="LONG")
            if signal.get('take_profit'):
                execute_limit_order(self.ib, self.contract, "SELL", quantity, signal['take_profit'])

        elif trade_type == "SHORT":
            logging.info(f"TradeExecutor: Initiating SHORT position for quantity {quantity}")
            execute_short_order(self.ib, self.contract, quantity, limit_price=price)
            if signal.get('stop_loss'):
                place_stop_loss_order(self.ib, self.contract, quantity, signal['stop_loss'], position_type="SHORT")
            if signal.get('take_profit'):
                execute_limit_order(self.ib, self.contract, "BUY", quantity, signal['take_profit'])

        elif trade_type == "EXIT":
            pos_type = signal.get('position_type', 'LONG')
            action = "SELL" if pos_type == "LONG" else "BUY"
            from execution.limit_order_execution_logic import Order
            order = Order()
            order.action = action
            order.orderType = "MKT"
            order.totalQuantity = quantity
            logging.info(f"TradeExecutor: Exiting position -> {action} {quantity} (market order)")
            self.ib.place_order(self.contract, order)

        else:
            logging.warning(f"Unknown trade signal type: {trade_type}")
