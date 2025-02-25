import sys
import time
import threading
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import Order
from ibapi.common import OrderId

def clean_order(order: Order) -> Order:
    """
    Force these attributes to exist (and be False).
    If we don't define them, IB Python API will try make_field(order.allOrNone)
    and crash if 'allOrNone' doesn't exist.
    """
    order.allOrNone = False
    order.eTradeOnly = False
    order.firmQuoteOnly = False
    return order

class DynamicBracketApp(EWrapper, EClient):
    def __init__(self):
        EWrapper.__init__(self)
        EClient.__init__(self, wrapper=self)

        self.next_order_id = None

        # Track parent info
        self.parent_order_id = None
        self.parent_fill_price = None
        self.parent_order_filled = False

        # Make sure we only place child orders once
        self.child_orders_placed = False

    def connect_and_start(self):
        print("Connecting to IB Gateway/TWS...")
        # Adjust port if you're on LIVE TWS (usually 7496).
        self.connect("127.0.0.1", 7497, clientId=9)

        # Start the reader thread
        api_thread = threading.Thread(target=self.run)
        api_thread.start()

        time.sleep(2)

        if not self.isConnected():
            print("Still not connected. Check TWS is open, port=7497, API enabled, no firewall blocks.")
            sys.exit(1)

        # Request the next valid ID
        self.reqIds(-1)

        # Wait until we have an order ID
        while self.next_order_id is None:
            print("Waiting for next valid order ID...")
            time.sleep(1)

        # Place the parent MARKET order
        self.place_parent_market_order()

    def create_mes_contract(self):
        contract = Contract()
        contract.symbol = "MES"
        contract.secType = "FUT"
        contract.exchange = "CME"
        contract.currency = "USD"
        # Example: March 2025
        contract.lastTradeDateOrContractMonth = "20250321"
        return contract

    def place_parent_market_order(self):
        self.parent_order_id = self.next_order_id
        self.next_order_id += 1

        contract = self.create_mes_contract()

        parent_order = Order()
        parent_order.orderId = self.parent_order_id
        parent_order.action = "BUY"
        parent_order.orderType = "MKT"
        parent_order.totalQuantity = 1
        parent_order.transmit = True  # send immediately

        clean_order(parent_order)

        print(f"Placing parent MARKET order (ID={self.parent_order_id})...")
        self.placeOrder(self.parent_order_id, contract, parent_order)

    def place_child_orders(self):
        """
        Instead of referencing the now-filled parent order,
        we place an OCA group with two orders: a limit (take-profit)
        and a stop (stop-loss). That way, TWS won't complain
        that we're modifying a filled parent. Also, we'll set
        transmit=True so they go live immediately.
        """
        contract = self.create_mes_contract()
        fill_price = self.parent_fill_price
        qty = 1

        # Example bracket logic for LONG
        take_profit_price = fill_price + 2.0
        stop_loss_price   = fill_price - 1.0

        # We'll create an OCA group so if one order fills, TWS cancels the other
        oca_group_name = "DYN_BRACKET_OCA"

        tp_id = self.next_order_id
        self.next_order_id += 1
        sl_id = self.next_order_id
        self.next_order_id += 1

        # TAKE-PROFIT (Limit)
        tp_order = Order()
        tp_order.orderId = tp_id
        tp_order.action = "SELL"
        tp_order.orderType = "LMT"
        tp_order.totalQuantity = qty
        tp_order.lmtPrice = take_profit_price
        tp_order.ocaGroup = oca_group_name
        tp_order.ocaType = 1  # 1 = CANCEL_WITH_BLOCK (typical OCA)
        tp_order.transmit = False  # We'll transmit with the stop

        clean_order(tp_order)

        # STOP-LOSS (Stop)
        sl_order = Order()
        sl_order.orderId = sl_id
        sl_order.action = "SELL"
        sl_order.orderType = "STP"
        sl_order.auxPrice = stop_loss_price
        sl_order.totalQuantity = qty
        sl_order.ocaGroup = oca_group_name
        sl_order.ocaType = 1
        sl_order.transmit = True  # This final child transmits the bracket

        clean_order(sl_order)

        print(f"\nPlacing OCA child orders (no parentId, but OCA linked):\n"
              f"  TAKE-PROFIT (ID={tp_id}) @ {take_profit_price}\n"
              f"  STOP-LOSS   (ID={sl_id}) @ {stop_loss_price}\n")

        self.placeOrder(tp_id, contract, tp_order)
        self.placeOrder(sl_id, contract, sl_order)

    # -------------------------
    # EWrapper EVENT HANDLERS
    # -------------------------

    def nextValidId(self, orderId: OrderId):
        super().nextValidId(orderId)
        self.next_order_id = orderId
        print(f"Received nextValidId: {orderId}")

    def orderStatus(self, orderId, status, filled, remaining,
                    avgFillPrice, permId, parentId, lastFillPrice,
                    clientId, whyHeld, mktCapPrice):
        print(f"orderStatus: ID={orderId}, Status={status}, "
              f"Filled={filled}, AvgPrice={avgFillPrice}")

        # If the parent order is FILLED (and we haven't placed children yet):
        if (orderId == self.parent_order_id 
            and status.upper() == "FILLED" 
            and not self.child_orders_placed):

            self.child_orders_placed = True
            self.parent_fill_price = avgFillPrice
            self.parent_order_filled = True

            print(f"Parent order {orderId} FILLED at {avgFillPrice}. Placing child orders now...")
            self.place_child_orders()

            # Give TWS a moment to process the child orders
            time.sleep(2)
            print("All orders placed. Exiting script now.")
            self.disconnect()
            sys.exit(0)

    def execDetails(self, reqId, contract, execution):
        super().execDetails(reqId, contract, execution)
        print(f"execDetails: {execution}")

    def error(self, reqId, errorCode, errorString, advancedOrderRejectJson=None):
        print(f"Error: reqId={reqId}, code={errorCode}, msg={errorString}")
        if advancedOrderRejectJson:
            print(f"AdvancedOrderRejectJson: {advancedOrderRejectJson}")

def main():
    app = DynamicBracketApp()
    app.connect_and_start()
    # We do NOT keep looping forever; 
    # we rely on the final sys.exit(0) after child orders are placed.

if __name__ == "__main__":
    main()
