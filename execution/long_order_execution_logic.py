import logging
from execution.limit_order_execution_logic import execute_limit_order, create_limit_order

try:
    from ibapi.order import Order
except ImportError:
    # Use the Order class from limit_order_execution_logic if available
    from execution.limit_order_execution_logic import Order

def execute_long_order(ib_connection, contract, quantity: int, limit_price: float = None):
    """
    Execute a long (buy) order. If limit_price is provided, places a limit buy; otherwise, a market buy.
    """
    if limit_price is not None:
        # Place a limit buy order at the given price
        execute_limit_order(ib_connection, contract, "BUY", quantity, limit_price)
    else:
        # Place a market buy order
        order = Order()
        order.action = "BUY"
        order.orderType = "MKT"
        order.totalQuantity = quantity
        logging.info(f"Executing market buy order for quantity {quantity}")
        ib_connection.place_order(contract, order)
