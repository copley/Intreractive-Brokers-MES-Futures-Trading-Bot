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
        self.ib = ib_connection
        self.contract = contract
        self.config = config  # store config for reference (e.g., for logging or risk management)

    def execute_trade(self, signal: dict):
        """
        Execute a trade based on the given signal.
        The signal dictionary is expected to have keys:
        - type: "LONG", "SHORT", or "EXIT"
        - quantity: amount to trade
        - price: desired entry price (None for market order)
        - stop_loss: stop-loss price for the trade (if any)
        - take_profit: take-profit price for the trade (if any)
        - position_type: for "EXIT" signals, indicates if exiting a LONG or SHORT
        """
        trade_type = signal.get('type')
        quantity = signal.get('quantity', 0)
        price = signal.get('price', None)
        if trade_type == "LONG":
            # Enter a long position
            logging.info(f"TradeExecutor: Initiating LONG position for quantity {quantity}")
            execute_long_order(self.ib, self.contract, quantity, limit_price=price)
            # Place stop-loss and take-profit orders if specified
            if signal.get('stop_loss'):
                place_stop_loss_order(self.ib, self.contract, quantity, signal['stop_loss'], position_type="LONG")
            if signal.get('take_profit'):
                # For take-profit on a long, place a limit sell
                execute_limit_order(self.ib, self.contract, "SELL", quantity, signal['take_profit'])
        elif trade_type == "SHORT":
            # Enter a short position
            logging.info(f"TradeExecutor: Initiating SHORT position for quantity {quantity}")
            execute_short_order(self.ib, self.contract, quantity, limit_price=price)
            if signal.get('stop_loss'):
                place_stop_loss_order(self.ib, self.contract, quantity, signal['stop_loss'], position_type="SHORT")
            if signal.get('take_profit'):
                # For take-profit on a short, place a limit buy (to cover)
                execute_limit_order(self.ib, self.contract, "BUY", quantity, signal['take_profit'])
        elif trade_type == "EXIT":
            # Exit an existing position (market order exit)
            pos_type = signal.get('position_type', 'LONG')
            action = "SELL" if pos_type == "LONG" else "BUY"
            order_price = signal.get('price', None)
            # Use market order to exit immediately
            from execution.limit_order_execution_logic import Order  # use Order class for market order
            order = Order()
            order.action = action
            order.orderType = "MKT"
            order.totalQuantity = quantity
            logging.info(f"TradeExecutor: Exiting position -> {action} {quantity} (market order)")
            self.ib.place_order(self.contract, order)
        else:
            logging.warning(f"Unknown trade signal type: {trade_type}")
