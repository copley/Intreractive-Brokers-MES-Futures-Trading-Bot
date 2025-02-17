import logging
try:
    from ibapi.order import Order
except ImportError:
    # Define a simple Order class if ibapi is not available (for simulation purposes)
    class Order:
        def __init__(self):
            self.action = None
            self.orderType = None
            self.totalQuantity = 0
            self.lmtPrice = None
        def __repr__(self):
            return f"<Order {self.orderType} {self.action} {self.totalQuantity}@{self.lmtPrice}>"

def create_limit_order(action: str, quantity: int, limit_price: float):
    """
    Helper to create a limit order object for IB or simulation.
    """
    order = Order()
    order.action = action
    order.orderType = "LMT"
    order.totalQuantity = quantity
    order.lmtPrice = limit_price
    return order

def execute_limit_order(ib_connection, contract, action: str, quantity: int, limit_price: float):
    """
    Execute a limit order (either BUY or SELL) at the specified price.
    """
    order = create_limit_order(action, quantity, limit_price)
    logging.info(f"Executing limit order: {action} {quantity} @ {limit_price}")
    ib_connection.place_order(contract, order)
