import logging
from execution.limit_order_execution_logic import execute_limit_order, create_limit_order

try:
    from ibapi.order import Order
except ImportError:
    from execution.limit_order_execution_logic import Order

def execute_short_order(ib_connection, contract, quantity: int, limit_price: float = None):
    """
    Execute a short (sell short) order. If limit_price is provided, places a limit sell; otherwise, a market sell.
    """
    if limit_price is not None:
        # Place a limit sell order at the given price
        execute_limit_order(ib_connection, contract, "SELL", quantity, limit_price)
    else:
        # Place a market sell order (for shorting or selling a long position)
        order = Order()
        order.action = "SELL"
        order.orderType = "MKT"
        order.totalQuantity = quantity
        logging.info(f"Executing market sell order for quantity {quantity}")
        ib_connection.place_order(contract, order)
