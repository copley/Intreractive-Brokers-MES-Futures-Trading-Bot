import logging

try:
    from ibapi.order import Order
except ImportError:
    from execution.limit_order_execution_logic import Order

def place_stop_loss_order(ib_connection, contract, quantity: int, stop_price: float, position_type: str = "LONG"):
    """
    Place a stop-loss order for an open position.
    For a LONG position, it will be a sell stop; for a SHORT position, a buy stop (to cover).
    """
    order = Order()
    if position_type.upper() == "LONG":
        order.action = "SELL"  # sell to exit long
    else:
        order.action = "BUY"   # buy to exit short
    order.orderType = "STP"
    order.totalQuantity = quantity
    order.auxPrice = stop_price  # auxPrice is the trigger price for stop orders in IB API
    logging.info(f"Placing stop-loss order for {position_type} position: {order.action} {quantity} @ stop {stop_price}")
    ib_connection.place_order(contract, order)
