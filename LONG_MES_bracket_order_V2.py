from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import Order
from ibapi.common import OrderId
import threading
import time

class BracketOrderApp(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.next_order_id = None
        self.parent_fill_price = None  # Track the fill price of the parent order
        self.parent_order_filled = False

    def connect_and_start(self):
        print("Connecting to IB Gateway/TWS...")
        self.connect("127.0.0.1", 7497, clientId=8)

        thread = threading.Thread(target=self.run)
        thread.start()

        time.sleep(1)  # Allow some time for connection to establish

        # Wait for the next valid order ID
        while self.next_order_id is None:
            print("Waiting for next valid order ID...")
            time.sleep(1)

        # Define the MES futures contract
        contract = self.create_mes_contract()

        # Place the short bracket order
        self.place_short_bracket_order(contract)

    def create_mes_contract(self):
        contract = Contract()
        contract.symbol = "MES"  # Micro E-mini S&P 500
        contract.secType = "FUT"  # Futures contract
        contract.exchange = "CME"  # Chicago Mercantile Exchange (CME)
        contract.currency = "USD"  # U.S. Dollar
        contract.lastTradeDateOrContractMonth = "202412"  # DEC 2024 contract
        return contract

    def place_short_bracket_order(self, contract):
        parent_order_id = self.next_order_id
        take_profit_order_id = parent_order_id + 1
        stop_loss_order_id = parent_order_id + 2

        # Create the market order (parent order)
        parent_order = Order()
        parent_order.orderId = parent_order_id
        parent_order.action = "SELL"
        parent_order.orderType = "MKT"  # Market order
        parent_order.totalQuantity = 1  # 1 MES contract
        parent_order.transmit = True  # Send the parent order immediately

        # Place the parent order
        self.placeOrder(parent_order_id, contract, parent_order)
        print("Parent order placed. Waiting for execution...")

        # Wait for the parent order to be executed and get the fill price
        while not self.parent_order_filled:
            time.sleep(0.5)

        # Set take-profit and stop-loss prices based on the fill price
        take_profit_price = self.parent_fill_price + 1.0  # Example: 1 point below the entry price
        stop_loss_price = self.parent_fill_price - 0.5  # Example: 0.5 points above the entry price

        # Create the take profit order (child order)
        take_profit_order = Order()
        take_profit_order.orderId = take_profit_order_id
        take_profit_order.action = "BUY"
        take_profit_order.orderType = "LMT"  # Limit order
        take_profit_order.totalQuantity = 1
        take_profit_order.lmtPrice = take_profit_price
        take_profit_order.parentId = parent_order_id  # Link to the parent
        take_profit_order.transmit = False  # Wait for the stop loss order

        # Create the stop loss order (child order)
        stop_loss_order = Order()
        stop_loss_order.orderId = stop_loss_order_id
        stop_loss_order.action = "BUY"
        stop_loss_order.orderType = "STP"  # Stop order
        stop_loss_order.totalQuantity = 1
        stop_loss_order.auxPrice = stop_loss_price
        stop_loss_order.parentId = parent_order_id  # Link to the parent
        stop_loss_order.transmit = True  # Transmit the whole bracket order

        # Send the child orders
        self.placeOrder(take_profit_order_id, contract, take_profit_order)
        self.placeOrder(stop_loss_order_id, contract, stop_loss_order)
        print("Short bracket order placed with take-profit and stop-loss.")

        # Update the next_order_id for future use
        self.next_order_id += 3

    def nextValidId(self, orderId: OrderId):
        super().nextValidId(orderId)
        self.next_order_id = orderId
        print(f"Next valid order ID: {orderId}")

    def execDetails(self, reqId, contract, execution):
        super().execDetails(reqId, contract, execution)
        print(f"Execution details: {execution}")
        if execution.orderId == self.next_order_id:
            self.parent_fill_price = execution.avgPrice  # Capture the executed price
            self.parent_order_filled = True  # Mark the parent as filled

    def orderStatus(self, orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
        print(f"OrderStatus. ID: {orderId}, Status: {status}, Filled: {filled}, AvgPrice: {avgFillPrice}")
        if orderId == self.next_order_id and status == "Filled":
            self.parent_fill_price = avgFillPrice
            self.parent_order_filled = True

    def error(self, reqId, errorCode, errorString, advancedOrderRejectJson=None):
        print(f"Error: {reqId}, {errorCode}, {errorString}")
        if advancedOrderRejectJson:
            print(f"Advanced Order Reject Info: {advancedOrderRejectJson}")

def main():
    app = BracketOrderApp()
    app.connect_and_start()

    # Keep the script running to listen for events
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Disconnecting...")
        app.disconnect()

if __name__ == "__main__":
    main()
